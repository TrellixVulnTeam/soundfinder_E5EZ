# Where is Sound

Tasks located in Projects tab - https://github.com/BrandonZupan/where-is-sound/projects

## Notes

-   Naming:

    -   Facing audience, left mic is Mic 1/A, right mic is Mic 2/B
    -   Right side is -900 to 0
    -   Left side is 0 to 900

-   Best measured mic distances:

    -   1m has worked for other people (16kHz-->2deg)
    -   75mm ideal for human speech
    -   250mm works as well
    -   Best case is to have three mics, offering 3 different distance ranges

-   Best measured ESP32 settings:

    -   32kHz sampling rate & 1024 samples/frame --> 940.0ms frame roundtrip on serial

-   Sampling Frequency vs TM4C Timer Period Mapping
    -   1 kHz: 79999
    -   2 kHz: 39999
    -   8 kHz: 9999
    -   16 kHz: 4999
    -   32 kHz: 2499
    -   48 kHz: 1665
