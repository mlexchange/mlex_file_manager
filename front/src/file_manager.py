import os 
import pathlib

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


def add_filenames_from_dir(dir_path, supported_formats, list_filename):
    '''
    Args:
        dir_path, str:                 full path of a directory
        supported_formats, list:   supported formats, e.g., ['tiff', 'tif', 'jpg', 'jpeg', 'png']
        list_filename, [str]:          list of file paths (full path, str)
    
    Returns:
        list_filename, [str]
    '''
    hidden_formats = ['DS_Store']
    root_path, list_dirs, filenames = next(os.walk(dir_path))
    for filename in filenames:
        exts = filename.split('.')
        if exts[-1] in supported_formats and exts[-1] not in hidden_formats and exts[-2] != '':
            filename = root_path + '/' + filename
            list_filename.append(filename)
            
    for dirname in list_dirs:
        new_dir_path = dir_path + '/' + dirname
        list_filename = add_filenames_from_dir(new_dir_path, supported_formats, list_filename)
    
    return list_filename


def filename_list(directory, format):
    '''
    Return a list of absolute file path (filtered by file formats) in a directory. 
    '''
    hidden_formats = ['DS_Store']
    files = []
    if format == 'dir':
        if os.path.exists(directory):
            for filepath in pathlib.Path(directory).glob('**/*'):
                if os.path.isdir(filepath):
                    files.append({'file_path': str(filepath.absolute()), 'file_type': 'dir'})
    else:
        format = format.split(',')
        for f_ext in format:
            if os.path.exists(directory):
                for filepath in pathlib.Path(directory).glob('**/{}'.format(f_ext)):
                    if os.path.isdir(filepath):
                        files.append({'file_path': str(filepath.absolute()), 'file_type': 'dir'})
                    else:
                        filename = str(filepath).split('/')[-1]
                        exts = filename.split('.')
                        if exts[-1] not in hidden_formats and exts[-2] != '':
                            files.append({'file_path': str(filepath.absolute()), 'file_type': 'file'})
    
    return files

