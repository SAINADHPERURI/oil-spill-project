import os
import glob
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from unet import UNet


# =========================
# CONFIG
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TRAIN_IMAGE_DIR = os.path.join(
    BASE_DIR, "patches", "train", "images"
)

TRAIN_MASK_DIR = os.path.join(
    BASE_DIR, "patches", "train", "masks"
)

MODEL_DIR = os.path.join(
    BASE_DIR, "models"
)

MODEL_PATH = os.path.join(
    MODEL_DIR, "oil_spill_unet.pth"
)

BATCH_SIZE = 4
EPOCHS = 20
LEARNING_RATE = 1e-4

DEVICE = torch.device("cpu")


# =========================
# DATASET
# =========================

class OilSpillDataset(Dataset):

    def __init__(self, image_dir, mask_dir):

        self.images = sorted(
            glob.glob(os.path.join(image_dir, "*.npy"))
        )

        self.mask_dir = mask_dir

        print(f"Loaded {len(self.images)} image patches")

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):

        image_path = self.images[idx]

        filename = os.path.basename(image_path)

        mask_path = os.path.join(
            self.mask_dir,
            filename
        )

        image = np.load(image_path).astype(np.float32)

        mask = np.load(mask_path).astype(np.float32)

        # Add channel dimension
        image = torch.from_numpy(image).unsqueeze(0)

        mask = torch.from_numpy(mask).unsqueeze(0)

        return image, mask


# =========================
# DICE LOSS
# =========================

class DiceLoss(nn.Module):

    def __init__(self, smooth=1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, predictions, targets):

        predictions = torch.sigmoid(predictions)

        predictions = predictions.view(-1)
        targets = targets.view(-1)

        intersection = (predictions * targets).sum()

        dice = (
            (2.0 * intersection + self.smooth)
            /
            (
                predictions.sum()
                + targets.sum()
                + self.smooth
            )
        )

        return 1.0 - dice


class CombinedLoss(nn.Module):

    def __init__(self):

        super().__init__()

        self.bce = nn.BCEWithLogitsLoss()
        self.dice = DiceLoss()

    def forward(self, predictions, targets):

        bce_loss = self.bce(predictions, targets)
        dice_loss = self.dice(predictions, targets)

        return bce_loss + dice_loss


# =========================
# TRAINING
# =========================

def main():

    os.makedirs(MODEL_DIR, exist_ok=True)

    print("===================================")
    print(" OIL SPILL U-NET TRAINING")
    print("===================================")

    print("Device:", DEVICE)

    dataset = OilSpillDataset(
        TRAIN_IMAGE_DIR,
        TRAIN_MASK_DIR
    )

    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0
    )

    model = UNet(
        in_channels=1,
        out_channels=1
    ).to(DEVICE)

    criterion = CombinedLoss()

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE
    )

    for epoch in range(EPOCHS):

        model.train()

        running_loss = 0.0

        for images, masks in loader:

            images = images.to(DEVICE)
            masks = masks.to(DEVICE)

            optimizer.zero_grad()

            predictions = model(images)

            loss = criterion(
                predictions,
                masks
            )

            loss.backward()

            optimizer.step()

            running_loss += loss.item()

        average_loss = (
            running_loss / len(loader)
        )

        print(
            f"Epoch [{epoch + 1}/{EPOCHS}] "
            f"Loss: {average_loss:.4f}"
        )

    torch.save(
        model.state_dict(),
        MODEL_PATH
    )

    print("\n===================================")
    print(" TRAINING COMPLETE")
    print("===================================")

    print("Model saved to:")
    print(MODEL_PATH)


if __name__ == "__main__":
    main()