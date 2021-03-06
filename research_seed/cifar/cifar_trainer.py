"""
This file runs the main training/val loop, etc... using Lightning Trainer"""
import os

from pytorch_lightning import Trainer
from pytorch_lightning.callbacks import ModelCheckpoint, EarlyStopping
from pytorch_lightning.logging import TestTubeLogger
from test_tube import Experiment

from argparse import ArgumentParser

import time

from cifar_model import BnnOnCIFAR10


def main(hparams):
    print(hparams)

    # init module
    model = BnnOnCIFAR10(hparams)

    logger = TestTubeLogger(
        save_dir=".",
        name="lightning_logs",
        version=time.strftime("%Y-%m-%d_%H-%M-%S"),
        debug=False,
        create_git_tag=False,
    )

    if hparams.restart_from_checkpoint:
        exp = Experiment(hparams.restart_from_checkpoint)
        trainer = Trainer(experiment=exp)

    else:
        hparams.debug = bool(hparams.debug)
        hparams.early_stopping = bool(hparams.early_stopping)

        if hparams.early_stopping:
            early_stop_callback = EarlyStopping(
                monitor="val_loss",
                min_delta=0.00,
                patience=3,
                verbose=False,
                mode="min",
            )
        else:
            early_stop_callback = None

        if hparams.save_weights_every_n == 0:
            checkpoint_callback = True
        else:
            ckpt_path = os.path.join(
                os.getcwd(), logger.name, f"version_{logger.version}", "checkpoints"
            )

            checkpoint_callback = ModelCheckpoint(
                filepath=ckpt_path,
                verbose=True,
                save_top_k=-1,
                prefix="",
                period=hparams.save_weights_every_n,
            )

        # most basic trainer, uses good defaults
        trainer = Trainer(
            max_nb_epochs=hparams.max_nb_epochs,
            gpus=hparams.gpus,
            distributed_backend="dp" if hparams.gpus != 1 else None,
            nb_gpu_nodes=hparams.nodes,
            show_progress_bar=True,
            overfit_pct=hparams.overfit_pct,
            fast_dev_run=hparams.debug,
            early_stop_callback=early_stop_callback,
            checkpoint_callback=checkpoint_callback,
            logger=logger,
        )

    trainer.fit(model)


if __name__ == "__main__":
    parser = ArgumentParser(add_help=False)
    parser.add_argument("--gpus", type=str, default=1)
    parser.add_argument("--nodes", type=int, default=1)
    parser.add_argument("--max_nb_epochs", default=500, type=int)
    parser.add_argument("--debug", default=0, type=int, choices=[0, 1])
    parser.add_argument("--overfit_pct", default=0.00, type=float)
    parser.add_argument("--restart-from-checkpoint", default=None, type=str)
    parser.add_argument("--early-stopping", default=0, type=int, choices=[0, 1])
    parser.add_argument("--num-data-loaders", default=0, type=int)
    parser.add_argument("--save-weights-every-n", default=0, type=int)

    # give the module a chance to add own params
    # good practice to define LightningModule specific params in the module
    parser = BnnOnCIFAR10.add_model_specific_args(parser)

    # parse params
    hparams = parser.parse_args()

    main(hparams)
