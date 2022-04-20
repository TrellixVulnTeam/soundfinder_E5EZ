# Python Receiver
Receives data from microcontroller for processing later

## Installing packages
Install packages with shell command `pip install -r requirements.txt`

## Receiver.py
Receives data from either a serial device or a file

### Importing
Import with:
```py
from receiver import Receiver
```

### Initializer
Specify data source, if the data is coming from a file, and the baud rate. 
`use_file` defaults to false and `baud_rate` defaults to 115200. 

#### Initializing for a serial device
```py
r = Receiver("COM27")
```

#### Initializing for a serial device and specifying baud rate
```py
r = Receiver("COM27", baud_rate=9600)
```

#### Initializing for using with a file
```py
r = Receiver ("random_data", use_file=True)
```

### Receiving data
Opens serial connection or file, receives a specified number of data, then 
closes the connection. This function is blocking and will not timeout. 

```py
r = Receiver("random_data", use_file=True)

data = r.receive(10)
```

The first column of data is the sample number, the second column is 
one channel, and the third column is the second channel. 
Data from specific channels can be accessed by indexing a specific 
column of data:
```py
index = data[:,0]
ch1 = data[:,1]
ch2 = data[:,2]
```