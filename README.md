differ
======

Creates a diff file between two zip files and combines the first zip file with the diff to recreate the second zip file


Examples
======
Create a diff between two APKs
```
./differ.py -g build561.apk build573.apk 561to573.diff
```

Combine a diff and original APK to create the final APK
```
./differ.py -c build561.apk 561to573.diff recreatedBuild573.apk
```