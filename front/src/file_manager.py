import os 
import pathlib
import copy
import glob
from functools import reduce

def move_a_file(source, destination):
    '''
    Args:
        source, str:          full path of a file from source directory
        destination, str:     full path of destination directory 
    '''
    pathlib.Path(destination).mkdir(parents=True, exist_ok=True)
    filename = source.split('/')[-1]
    new_destination = destination + '/' + filename
    os.rename(source, new_destination)


def move_dir(source, destination):
    '''
    Args:
        source, str:          full path of source directory
        destination, str:     full path of destination directory 
    '''
    dir_path, list_dirs, filenames = next(os.walk(source))
    original_dir_name = dir_path.split('/')[-1]
    destination = destination + '/' + original_dir_name
    pathlib.Path(destination).mkdir(parents=True, exist_ok=True)
    for filename in filenames:
        file_source = dir_path + '/' + filename  
        move_a_file(file_source, destination)
    
    for dirname in list_dirs:
        dir_source = dir_path + '/' + dirname
        move_dir(dir_source, destination)


def _paths_from_dir(dir_path, patterns=['**/*'], sort=False):
    #paths = glob.glob(dir_path+'/**/*', recursive=True)
    paths = list(reduce(lambda list1, list2: list1 + list2, (glob.glob(str(dir_path)+'/'+t, recursive=True) for t in patterns)))
    if sort:
        paths.sort()
    
    return paths


def filenames_from_dir(dir_path, formats, sort=False):
    '''
    Args:
        dir_path, str:            full path of a directory
        formats, list:  supported formats, e.g., ['tiff', 'tif', 'jpg', 'jpeg', 'png']
        sort, boolean:            whether ordered or not, default False 
    Returns:
        List[str]:      a list of filenames (does not contain folders) 
    '''
    patterns = ['**/*.'+t for t in formats]
    return _paths_from_dir(dir_path, patterns, sort)


def paths_from_dir(dir_path, form, sort=False):
    '''
    Args:
        directory, str:     full path of a directory
        form, str:          A supported format in ['dir', '*', '*.png', '*.jpg,*jpeg', '*.tif,*tiff', '*.txt', '*.csv']
        sort, boolean:      whether ordered or not, default False 
    Return:
        List[dict]:         a full list of absolute file path (filtered by file formats) inside a directory.
    '''
    paths = []
    if form == 'dir' or form == '*':
        directories = _paths_from_dir(dir_path,['**/'], sort) # include the root dir path
        for directory in directories[1:]:      # exclude the root dir path
            paths.append({'file_path': directory[:-1], 'file_type': 'dir'})
        if form == '*':
            patterns = ['**/*.png', '**/*.jpg', '**/*jpeg', '**/*.tif', '**/*tiff', '**/*.txt', '**/*.csv']
            fnames = _paths_from_dir(dir_path, patterns, sort)
            for fname in fnames:
                paths.append({'file_path': fname, 'file_type': 'file'})
    else:
        formats = form.split(',')
        patterns = ['**/*.'+e[2:] for e in formats]
        fnames = _paths_from_dir(dir_path, patterns, sort)
        for fname in fnames:
            paths.append({'file_path': fname, 'file_type': 'file'})
            
    return paths


def docker_to_local_path(paths, docker_home, local_home, path_type='list-dict'):
    '''
    Args:
        paths:              docker file paths
        docker_home, str:   full path of home dir (ends with '/') in docker environment
        local_home, str:    full path of home dir (ends with '/') mounted in local machine
        path_type:
            list-dict, default:  a list of dictionary (docker paths), e.g., [{'file_path': 'docker_path1'},{...}]
            str:                a single file path string
    Return: 
        str or List[dict]:   replace docker path with local path, the same data structure as paths
    '''
    if path_type == 'list-dict':
        files = copy.deepcopy(paths)
        for file in files:
            if not file['file_path'].startswith(local_home):
                file['file_path'] = local_home + file['file_path'].split(docker_home)[-1]
    
    if path_type == 'str':
        if not paths.startswith(local_home):
            files = local_home + paths.split(docker_home)[-1]
        else:
            files = paths
        
    return files


def local_to_docker_path(paths, docker_home, local_home, path_type='list'):
    '''
    Args:
        paths:             selected local (full) paths 
        docker_home, str:  full path of home dir (ends with '/') in docker environment
        local_home, str:   full path of home dir (ends with '/') mounted in local machine
        path_type:
            list:          a list of path string
            str:           single path string 
    Return: 
        list or str:    replace local path with docker path, the same data structure as paths
    '''
    if path_type == 'list':
        files = []
        for i in range(len(paths)):
            if not paths[i].startswith(docker_home):
                files.append(docker_home + paths[i].split(local_home)[-1])
            else:
                files.append(paths[i])
    
    if path_type == 'str':
        if not paths.startswith(docker_home):
            files = docker_home + paths.split(local_home)[-1]
        else:
            files = paths

    return files
