from typing import Tuple
import torch
import torch.nn as nn
import whisper
from whisper.audio import HOP_LENGTH, N_FFT, N_SAMPLES
from funasr.register import tables
from torch.nn.utils.rnn import pad_sequence


@tables.register("frontend_classes", "WhisperFrontend")
class WhisperFrontend(nn.Module):
    """Speech Representation Using Encoder Outputs from OpenAI's Whisper Model:

    URL: https://github.com/openai/whisper
    """

    def __init__(
            self,
            fs: int = 16000,
            whisper_model: str = None,
            do_pad_trim: bool = True,
            n_mels: int = 80,
    ):
        super().__init__()
        assert fs == 16000
        self.fs = fs

        self.n_fft = N_FFT
        self.win_length = N_FFT
        self.hop_length = HOP_LENGTH
        self.pad_samples = N_SAMPLES
        self.frame_shift = self.hop_length
        self.lfr_n = 1
        self.n_mels = n_mels
        if whisper_model == "large-v3" or whisper_model == "large":
            self.n_mels = 128

        self.mel_filters = whisper.audio.mel_filters
        self.do_pad_trim = do_pad_trim
        if do_pad_trim:
            self.pad_or_trim = whisper.pad_or_trim

        # assert whisper_model in whisper.available_models()

    def output_size(self) -> int:
        return self.n_mels

    def log_mel_spectrogram(
            self,
            audio: torch.Tensor,
            ilens: torch.Tensor = None,
    ) -> torch.Tensor:
        window = torch.hann_window(self.win_length).to(audio.device)
        stft = torch.stft(
            audio, self.n_fft, self.hop_length, window=window, return_complex=True
        )

        # whisper deletes the last frame by default (Shih-Lun)
        magnitudes = stft[..., :-1].abs() ** 2

        filters = self.mel_filters(audio.device, self.n_mels)
        mel_spec = filters @ magnitudes

        log_spec = torch.clamp(mel_spec, min=1e-10).log10()

        if ilens is not None:
            olens = ilens // self.hop_length
        else:
            olens = None

        log_spec = torch.maximum(
            log_spec,
            log_spec.view(audio.size(0), -1).max(dim=-1)[0][:, None, None] - 8.0,
        )
        log_spec = (log_spec + 4.0) / 4.0

        return log_spec, olens

    def forward(
            self, input: torch.Tensor, input_lengths: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        batch_size = input.size(0)
        feats = []
        feats_lens = []
        for i in range(batch_size):
            if self.do_pad_trim:
                feat = self.pad_or_trim(input[i], self.pad_samples)
            else:
                feat = input[i]
            feat, feat_len = self.log_mel_spectrogram(feat[None, :], input_lengths[0])
            feats.append(feat[0])
            feats_lens.append(feat_len)
        feats_lens = torch.as_tensor(feats_lens)

        if batch_size == 1:
            feats_pad = feats[0][None, :, :]
        else:
            feats_pad = pad_sequence(feats,
                                     batch_first=True,
                                     padding_value=0.0)

        return feats_pad, feats_lens