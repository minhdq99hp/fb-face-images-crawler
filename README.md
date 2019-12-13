# fb-face-images-crawler
Using Selenium to get face images for training model.

## Client
User use the app FBCrawler to login and start the crawler.

The crawler will login using the given email/pass. It will go to the friend list then crawl all the ID.

-> Friends' IDs and User's ID.

The crawler POST request to server to get the filtered IDs.

After having the filtered IDs, the crawler continue to crawl the user's photos. Use the aria-label to filter the image that doesn't contain people. 
(Also concern using some ML algorithms or FB tag feature to filter)

-> fbid of photos.

Open each image to get the source of photos. (This consume many time, so that is why we need to use PhantomJS)

-> src


Now, use multithreading to spawn worker to download all the images.

Finally, upload all the images to the server.
## Server
- Manage the database
- Response to POST requests from clients.

Requests:
1. Filter ID
    
    Input: IDs
    Output: Filtered IDs

2. Upload photos
    
    Check then add photos to dataset.

## Target
Build a dataset which have the form:
```
dataset/
    ID1/
        raw/
            {fbid}.jpg
            ...
        filtered/
            0001.jpg
            0002.jpg
            ...
    ID2/...
    ...
```
