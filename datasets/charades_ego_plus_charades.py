"""
    Dataset loader that combines Charadesego and Charades
    train and val loaders are concatenated
    Charades includes a [x, x, x] transform to match the input to charadesego
    labels for Charades are negative to distinguish between them
"""
import torchvision.transforms as transforms
from torch.utils.data.dataset import ConcatDataset
from datasets.charades import Charades
from datasets.charades_ego import CharadesEgo
import copy
import torch


class CharadesMeta(Charades):
    def __init__(self, *args, **kwargs):
        super(CharadesMeta, self).__init__(*args, **kwargs)

    def get_item(self, index):
        ims, target, meta = super(CharadesMeta, self).__getitem__(index)
        meta.update({'thirdtime': 0,
                     'firsttime_pos': 0,
                     'firsttime_neg': 0,
                     'n': 0,
                     'n_ego': 0,
                     })
        if self.split == 'val_video':
            return ims, target, meta
        else:
            return [ims, ims, ims], target, meta


class CharadesEgoMeta(CharadesEgo):
    def __init__(self, *args, **kwargs):
        super(CharadesEgoMeta, self).__init__(*args, **kwargs)

    def get_item(self, index):
        ims, target, meta = super(CharadesEgoMeta, self).__getitem__(index)
        newtarget = torch.IntTensor(self.num_classes).zero_()
        newtarget[0] = target
        meta['time'] = 0
        return ims, newtarget, meta


class CharadesEgoPlusCharades(CharadesMeta):
    @classmethod
    def get(cls, args, splits=('train', 'val', 'val_video')):
        newargs = copy.deepcopy(args)
        vars(newargs).update({
            'train_file': args.train_file.split(';')[1],
            'val_file': args.val_file.split(';')[1],
            'data': args.data.split(';')[1]})
        vars(args).update({
            'train_file': args.train_file.split(';')[0],
            'val_file': args.val_file.split(';')[0],
            'data': args.data.split(';')[0]})

        if 'train' in splits or 'val' in splits:
            train_datasetego, val_datasetego, _ = CharadesEgoMeta.get(args, splits=splits)
        else:
            train_datasetego, val_datasetego = None, None
        train_dataset, val_dataset, valvideo_dataset = super(CharadesEgoPlusCharades, cls).get(newargs, splits=splits)

        if 'train' in splits:
            train_dataset.target_transform = transforms.Lambda(lambda x: -x)
            train_dataset = ConcatDataset([train_dataset] + [train_datasetego] * 3)  # magic number to balance
        if 'val' in splits:
            val_dataset.target_transform = transforms.Lambda(lambda x: -x)
            val_dataset = ConcatDataset([val_dataset] + [val_datasetego] * 3)
        return train_dataset, val_dataset, valvideo_dataset
