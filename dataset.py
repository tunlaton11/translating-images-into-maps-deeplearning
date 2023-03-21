import os
import numpy as np
from PIL import Image
from torch.utils.data import Dataset
from torchvision.transforms.functional import to_tensor

from nuscenes import NuScenes
import nuscenes_utilities as nusc_utils


class NuSceneDataset(Dataset):
    def __init__(
        self,
        nuscenes_dir: str,
        nuscenes_version: str,
        label_dir: str,
        start_scene_index: int,
        end_scene_index: int,
        image_size=(200, 196),
        transform=None,
    ):
        self.nuscenes = NuScenes(nuscenes_version, nuscenes_dir)
        self.label_dir = label_dir
        self.image_size = image_size
        self.get_tokens(start_scene_index, end_scene_index)

    def get_tokens(
        self,
        start_scene_index: int,
        end_scene_index: int,
        scene_names=None,
    ):
        self.tokens = list()

        # Iterate over scenes
        for scene in self.nuscenes.scene[start_scene_index:end_scene_index]:

            # # Ignore scenes which don't belong to the current split
            # if scene_names is not None and scene["name"] not in scene_names:
            #     continue

            # Iterate over samples
            for sample in nusc_utils.iterate_samples(
                self.nuscenes, scene["first_sample_token"]
            ):

                self.tokens.append(sample["data"]["CAM_FRONT"])

        return self.tokens

    def __len__(self):
        return len(self.tokens)

    def __getitem__(self, index: int):
        token = self.tokens[index]
        image = self.load_image(token)
        labels, mask = self.load_labels(token)
        return image, labels, mask

    def load_image(self, token: str):

        # Load image as a PIL image
        image = Image.open(self.nuscenes.get_sample_data_path(token))

        # Resize to input resolution
        image = image.resize(self.image_size)

        # Convert to a torch tensor
        return to_tensor(image)

    def load_labels(self, token: str):

        # Load label image as a torch tensor
        label_path = os.path.join(self.label_dir, token + ".png")
        encoded_labels = to_tensor(Image.open(label_path)).long()

        # Decode to binary labels
        num_class = len(nusc_utils.NUSCENES_CLASS_NAMES)
        labels = nusc_utils.decode_binary_labels(encoded_labels, num_class + 1)
        labels, mask = labels[:-1], ~labels[-1]

        return labels, mask
