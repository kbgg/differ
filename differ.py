#!/usr/bin/python
import sys, getopt, hashlib, os, os.path, shutil, zipfile, tarfile, json

def main(argv):
    generate = False
    originalFile = ''
    newFile = ''
    diffFile = ''
    outputFile = ''

    try:
        opts, args = getopt.getopt(argv,'gc',[])
    except getopt.GetoptError:
        print 'differ.py [-g <originalfile> <newfile> <output>] or [-c <originalfile> <diff> <output>]'
        sys.exit(2)
    if len(args) != 3:
        print 'differ.py [-g <originalfile> <newfile> <output>] or [-c <originalfile> <diff> <output>]'
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-g'):
            generate = True
            originalFile = args[0]
            newFile = args[1]
            outputFile = args[2]
            generateDiff(originalFile, newFile, outputFile)
        elif opt in ('-c'):
            generate = False
            originalFile = args[0]
            diffFile = args[1]
            outputFile = args[2]    
            combineDiff(originalFile, diffFile, outputFile)

def combineDiff(original, diff, output):
    with zipfile.ZipFile(original) as zf:
        zf.extractall('originalTemp')
    tfile = tarfile.open(diff, 'r:gz')
    tfile.extractall(path='diffTemp')

    changesFile = open('diffTemp/diff/changes.json', 'r')
    changes = changesFile.read()
    changesFile.close()

    changes = json.loads(changes)

    for deleted in changes['deleted']:
        print 'REMOVED ' + deleted['subdir'] + '/' + deleted['file']
        path = 'originalTemp' + deleted['subdir'] + '/' + deleted['file']
        os.remove(path)

    for added in changes['added']:
        print 'ADDED ' + added['subdir'] + '/' + added['file']
        relativePath = added['subdir'] + '/' + added['file']
        shutil.copy('diffTemp/diff' + relativePath, 'originalTemp' + relativePath)

    for modified in changes['modified']:
        print 'MODIFIED ' + modified['subdir'] + '/' + modified['file']
        relativePath = modified['subdir'] + '/' + modified['file']
        shutil.copy('diffTemp/diff' + relativePath, 'originalTemp' + relativePath)

    shutil.make_archive('final', format='zip', root_dir='originalTemp') 
    shutil.move('final.zip', output)

    shutil.rmtree('diffTemp')
    shutil.rmtree('originalTemp')
    print 'Done'

def generateDiff(original, new, output):
    originalDir = '.' + original.replace('.', '')
    newDir = '.' + new.replace('.', '')

    with zipfile.ZipFile(original) as zf:
        zf.extractall(originalDir)
    with zipfile.ZipFile(new) as zf:
        zf.extractall(newDir)

    diff = spotDifferences(originalDir, newDir)

    if not os.path.exists('diff'):
        os.makedirs('diff')

    for modifiedFile in diff['modified']:
        subdirPath = 'diff' + modifiedFile['subdir']
        filePath = modifiedFile['subdir'] + '/' + modifiedFile['file']
        if not os.path.exists(subdirPath):
            os.makedirs(subdirPath)
        shutil.copy2(newDir + filePath, 'diff' + filePath)

    for addedFile in diff['added']:
        subdirPath = 'diff' + addedFile['subdir']
        filePath = addedFile['subdir'] + '/' + addedFile['file']
        if not os.path.exists(subdirPath):
            os.makedirs(subdirPath)
        shutil.copy2(newDir + filePath, 'diff' + filePath)

    changes = open('diff/changes.json', 'wb')
    changes.write(json.dumps(diff))
    changes.close()

    tar = tarfile.open(output, 'w:gz')
    tar.add('diff')
    tar.close()

    shutil.rmtree('diff')
    shutil.rmtree(originalDir)
    shutil.rmtree(newDir)
    print 'Done'

def spotDifferences(original, new):
    modified = []
    deleted = []
    added = []

    for subdir, dirs, files in os.walk(original):
        for file in files:
            originalFilePath = subdir + '/' + file
            newFilePath = originalFilePath.replace(original, new)
            originalFile = open(originalFilePath, 'r')
            if os.path.isfile(newFilePath):
                newFile = open(newFilePath, 'r')
                originalMd5 = md5(originalFile)
                newMd5 = md5(newFile)
                if not originalMd5 == newMd5:
                    relativePath = getRelativePath(subdir)
                    print 'MODIFIED ' + relativePath + '/' + file
                    modified.append({'subdir': relativePath, 'file': file})
            else:
                relativePath = getRelativePath(subdir)
                print 'REMOVED ' + relativePath + '/' + file
                deleted.append({'subdir': relativePath, 'file': file})

    for subdir, dirs, files in os.walk(new):
        for file in files:
            newFilePath = subdir + '/' + file
            originalFilePath = newFilePath.replace(new, original)
            if not os.path.isfile(originalFilePath):
                relativePath = getRelativePath(subdir)
                print 'ADDED ' + relativePath + '/' + file
                added.append({'subdir': relativePath, 'file': file})

    return {'modified': modified, 'deleted': deleted, 'added': added}

def getRelativePath(path):
    folders=[]
    while 1:
        path, folder = os.path.split(path)
        if folder != '':
            folders.append(folder)
        else:
            if path != '':
                folders.append(path)
            break
    folders.reverse()
    
    relativePath = ''
    for i in range(1, len(folders)):
        relativePath += ('/' + folders[i])
    return relativePath

def md5(f, block_size=2**20):
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()

def zipdir(path, zip):
    for root, dirs, files in os.walk(path):
        for file in files:
            zip.write(os.path.join(root, file))

if __name__ == '__main__':
   main(sys.argv[1:])