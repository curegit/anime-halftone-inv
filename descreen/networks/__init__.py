from abc import ABC, abstractmethod
from numpy import ndarray, pad
from torch import Tensor
from torch.nn import Module
from ..utilities import range_chunks


class AbsModule(ABC, Module):
    @abstractmethod
    def forward(self, x: Tensor) -> Tensor:
        raise NotImplementedError()

    @property
    def multiple_of(self) -> int:
        return 1

    @abstractmethod
    def output_size(self, input_size: int) -> int:
        raise NotImplementedError()

    @abstractmethod
    def input_size(self, output_size: int) -> int:
        raise NotImplementedError()

    def reduced_padding(self, input_size: int):
        output_size = self.output_size(input_size)
        assert (input_size - output_size) % 2 == 0
        return (input_size - output_size) // 2

    def required_padding(self, output_size: int):
        input_size = self.input_size(output_size)
        assert (input_size - output_size) % 2 == 0
        return (input_size - output_size) // 2

    def patch(self, x: ndarray, input_patch_size: int, *, pad_mode: str = "symmetric", **kwargs):
        if input_patch_size % self.multiple_of != 0:
            raise RuntimeError()
        out_patch_size = self.output_size(input_patch_size)
        p = self.required_padding(out_patch_size)
        height, width = x.shape[-2:]
        qh = height % self.multiple_of
        qw = width % self.multiple_of
        y = pad(x, (*([(0, 0)] * (x.ndim - 2)), (p, qh + p), (p, qw + p)), mode=pad_mode, **kwargs)
        h_crop = slice(p, height + p)
        w_crop = slice(p, width + p)
        return y, self.patch_slices(height + qh, width + qw, out_patch_size), (h_crop, w_crop)

    def patch_slices(self, height: int, width: int, output_patch_size: int):
        for h_start, h_stop in range_chunks(height, output_patch_size):
            for w_start, w_stop in range_chunks(width, output_patch_size):
                h_pad = self.required_padding(h_stop - h_start)
                w_pad = self.required_padding(w_stop - w_start)
                h_slice = slice(h_start - h_pad + h_pad, h_stop + h_pad * 2)
                w_slice = slice(w_start - w_pad + w_pad, w_stop + w_pad * 2)
                h_dest_slice = slice(h_start + h_pad, h_stop - h_pad)
                w_dest_slice = slice(w_start + w_pad, w_stop - w_pad)
                yield (h_slice, w_slice), (h_dest_slice, w_dest_slice)
