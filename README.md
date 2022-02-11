# MLExchange File Manager

Simple labeling application with a Dash UI.

## Running
```
docker-compose up --build
```

## Ingest data with MLExchange file manager
Put your dataset inside the **data folder** or use **MLExchange data connector** to transfer data to this folder (in future). 
This folder is mounted to the working directory in the container, and it is your **home data dir (HOME)**. 
Then go to the webpage and click on **Open File Manager** to lauch MLExchange file manager. It offers several options for users to ingest/manipualte data.   

1. Upload data from **Drag and Drop** to home data dir. 
Upload either a single file or a zip file (files) through drag and drop.
User can then browse the newly added files/folder in the path table and move them to a new directory inside HOME.  

2. Move data to a new directory:  
Input the destination directory (relative to root path) and select the files/folder from **File Table**. Then click on **Move** button. 
The selected files/dirs will be (recursively) moved into the new directory and the original dirs will be automatically deleted. 
If no input, files/dirs will be moved to **HOME**.
**Please note that folders of the same name (from different dirs) will be merged**.  

3. Browse files or directories in the **HOME** and import the selected files:   
After selecting which files or directories and filtering the display by format, click on **Import Selected Files or Directories** button on the right side. 
When importing a directory, you can import **only** files of a specific format by using the rightmost dropdown menu.  

4. Deleting files or directories:   
The selected file paths can be deleted by clicking **Delete the Selected** button. User must click on **Import** button again to ingest the newly selected files/paths. 
