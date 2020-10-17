import torch, os, torch.utils.data as data
import torchvision
import torchvision.transforms as transforms
from tqdm import tqdm
import numpy as np
import h5py
from PIL import Image
import io

class HDF5Dataset(data.Dataset):
    def __init__(self, data_path, key, transform):
        self.data_path = data_path
        self.key = key
        self.transform = transform

        # find classes
        self.h5_file = h5py.File(data_path, mode='r')
        self.classes = self._find_classes()
        self.class_to_idx = {} 
        for i, class_ in enumerate(self.classes):
            self.class_to_idx[class_] = i

        # find all files
        self.all_files = self._find_files()
        self.h5_file.close()

    def _find_classes(self):
        return list(self.h5_file[self.key].keys())        

    def _find_files(self):
        all_files = []
        for class_ in self.classes:
            files = list(self.h5_file[self.key][class_])
            for filename in files:
                path = self.key + "/" + class_ + "/" + filename
                all_files.append((path, self.class_to_idx[class_]))
        
        return all_files

    def __len__(self):
        return len(self.all_files)

    def __getitem__(self, index):
        h5_file = h5py.File(self.data_path, mode='r')
        path, class_ = self.all_files[index]

        # read byte array
        byte_arr = np.array(h5_file[path])
        img = Image.open(io.BytesIO(byte_arr))
        h5_file.close()

        if self.transform is not None: img = self.transform(img)
        return img, class_


########################################################################
# Define a Convolution Neural Network
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# Copy the neural network from the Neural Networks section before and modify it to
# take 3-channel images (instead of 1-channel images as it was defined).

import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models

# <<<<<<<<<<<<<<<<<<<<< EDIT THE MODEL DEFINITION >>>>>>>>>>>>>>>>>>>>>>>>>>
# Try experimenting by changing the following:
# 1. number of feature maps in conv layer
# 2. Number of conv layers
# 3. Kernel size
# etc etc.,

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()

        self.conv1 = nn.Conv2d(in_channels=3, out_channels=64, kernel_size=5)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.conv2 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=5)
        self.conv3 = nn.Conv2d(in_channels=128, out_channels=256, kernel_size=5)
        self.fc1 = nn.Linear(in_features=256, out_features=256)
        self.fc2 = nn.Linear(in_features=256, out_features=128)
        self.fc3 = nn.Linear(in_features=128, out_features=20)      # change out_features according to number of classes

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        x = F.avg_pool2d(x, kernel_size=x.shape[2:])
        x = x.view(x.shape[0], -1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x

################### DO NOT EDIT THE BELOW CODE!!! #######################

########################################################################
# Train the network
# ^^^^^^^^^^^^^^^^^^^^

def train(epoch, trainloader, optimizer, criterion):
    running_loss = 0.0
    for i, data in enumerate(tqdm(trainloader), 0):
        # get the inputs
        inputs, labels = data
        if torch.cuda.is_available():
            inputs, labels = inputs.cuda(), labels.cuda()

        # zero the parameter gradients
        optimizer.zero_grad()

        # forward + backward + optimize
        outputs = net(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        # print statistics
        running_loss += loss.item()

    print('epoch %d training loss: %.3f' %
            (epoch + 1, running_loss / (len(trainloader))))
    
########################################################################
# Let us look at how the network performs on the test dataset.

def test(testloader, model):
    correct = 0
    total = 0
    with torch.no_grad():
        for data in tqdm(testloader):
            images, labels = data
            if torch.cuda.is_available():
                images, labels = images.cuda(), labels.cuda()        
            outputs = net(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    print('Accuracy of the network on the test images: %d %%' % (
                                    100 * correct / total))

#########################################################################
# get details of classes and class to index mapping in a directory
def find_classes(dir):
    classes = [d for d in os.listdir(dir) if os.path.isdir(os.path.join(dir, d))]
    classes.sort()
    class_to_idx = {classes[i]: i for i in range(len(classes))}
    return classes, class_to_idx


def classwise_test(testloader, model):
########################################################################
# class-wise accuracy

    classes, _ = trainset.classes
    n_class = len(classes) # number of classes

    class_correct = list(0. for i in range(n_class))
    class_total = list(0. for i in range(n_class))
    with torch.no_grad():
        for data in tqdm(testloader):
            images, labels = data
            if torch.cuda.is_available():
                images, labels = images.cuda(), labels.cuda()        
            outputs = net(images)
            _, predicted = torch.max(outputs, 1)
            c = (predicted == labels).squeeze()
            for i in range(4):
                label = labels[i]
                class_correct[label] += c[i].item()
                class_total[label] += 1

    for i in range(n_class):
        print('Accuracy of %10s : %2d %%' % (
            classes[i], 100 * class_correct[i] / class_total[i]))


if __name__ == '__main__':

    num_epochs = 50         # desired number of training epochs.
    learning_rate = 0.001   

    ########################################################################
    # The output of torchvision datasets are PILImage images of range [0, 1].

    # Apply necessary image transfromations here 

    transform = transforms.Compose([ #torchvision.transforms.RandomHorizontalFlip(p=0.5),
                                    #torchvision.transforms.RandomAffine(degrees=(-10, 10), translate=(0.1, 0.1), scale=(0.8, 1.2)),
                                    transforms.ToTensor(),
                                    transforms.Normalize(mean=[0.5,0.5,0.5], std=[0.5, 0.5, 0.5])])
    print(transform)

    data_path = 'data_to_pth/dataset_1.hdf5' # put path of training dataset

    workers = 2
    trainset = HDF5Dataset(data_path=data_path, key='train', transform=transform)
    trainloader = torch.utils.data.DataLoader(trainset, batch_size=4,
                                            shuffle=True, num_workers=workers)

    valset = HDF5Dataset(data_path=data_path, key='val', transform=transform)
    valloader = torch.utils.data.DataLoader(valset, batch_size=4,
                                            shuffle=False, num_workers=workers)

    testset = HDF5Dataset(data_path=data_path, key='test', transform=transform)
    testloader = torch.utils.data.DataLoader(testset, batch_size=4,
                                            shuffle=False, num_workers=workers)
                                            
    #net = ResNet()
    net = Net()

    # transfer the model to GPU
    if torch.cuda.is_available():
        net = net.cuda()

    ########################################################################
    # Define a Loss function and optimizer
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    # Let's use a Classification Cross-Entropy loss and SGD with momentum.

    import torch.optim as optim
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(net.parameters(), lr=learning_rate, momentum=0.9, weight_decay=5e-4)

    num_params = np.sum([p.nelement() for p in net.parameters()])
    print(num_params, ' parameters')

    print('Start Training')
    os.makedirs('./models', exist_ok=True)

    for epoch in range(num_epochs):  # loop over the dataset multiple times
        print('epoch ', epoch + 1)
        train(epoch, trainloader, optimizer, criterion)
        test(valloader, net)
        classwise_test(valloader, net)
        # save model checkpoint 
        torch.save(net.state_dict(), './models/model-'+str(epoch)+'.pth')      

    print('performing test')
    test(testloader, net)
    classwise_test(testloader, net)

    print('Finished Training')


