#!/usr/bin/env python3
"""Export ONNX autonome — contourne les bugs de torch 2.13.

- `dynamic_axes` + `dynamo=False` (exporteur legacy) : sans cela torch.export
  fige l'axe des phonèmes et la voix reste muette au-delà d'une phrase courte.
- Modèle mono-speaker : on n'expose PAS d'entrée `sid` (piper n'en envoie pas).
- Le résultat est ré-embarqué en un seul fichier .onnx.
"""
import argparse, logging
from pathlib import Path

import torch
import onnx

from piper.train.vits.lightning import VitsModel

logging.basicConfig(level=logging.INFO)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--output-file", required=True)
    args = ap.parse_args()

    torch.manual_seed(1234)
    model = VitsModel.load_from_checkpoint(args.checkpoint, map_location="cpu")
    model_g = model.model_g
    model_g.eval()
    with torch.no_grad():
        model_g.dec.remove_weight_norm()

    def infer_forward(text, text_lengths, scales):
        noise_scale = scales[0]
        length_scale = scales[1]
        noise_scale_w = scales[2]
        audio = model_g.infer(
            text, text_lengths,
            noise_scale=noise_scale, length_scale=length_scale,
            noise_scale_w=noise_scale_w,
        )[0].unsqueeze(1)
        return audio

    model_g.forward = infer_forward

    num_symbols = model_g.n_vocab
    dummy_length = 50
    sequences = torch.randint(low=0, high=num_symbols, size=(1, dummy_length), dtype=torch.long)
    sequence_lengths = torch.LongTensor([sequences.size(1)])
    scales = torch.FloatTensor([0.667, 1.0, 0.8])
    dummy_input = (sequences, sequence_lengths, scales)

    torch.onnx.export(
        model=model_g,
        args=dummy_input,
        f=args.output_file,
        verbose=False,
        opset_version=15,
        input_names=["input", "input_lengths", "scales"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size", 1: "phonemes"},
            "input_lengths": {0: "batch_size"},
            "output": {0: "batch_size", 2: "time"},
        },
        dynamo=False,
    )

    m = onnx.load(args.output_file)
    onnx.save(m, args.output_file, save_as_external_data=False)
    Path(args.output_file + ".data").unlink(missing_ok=True)
    logging.info("Exporté : %s", args.output_file)


if __name__ == "__main__":
    main()
