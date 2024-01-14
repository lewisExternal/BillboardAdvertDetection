# Billboard advert detection 

As the adoption of augmented reality (AR) headsets proliferates, the ways in which consumers will experience content will change considerably, which means a radical shift away from the current state of billboard advertising.

This is to show how to create a computer vision model for applications such as ad-blocking in everyday life.

![test_1](https://github.com/lewisExternal/graveYardPrivatePublish/assets/81447748/739ea6d3-3087-410c-95f9-7c78e349162e)
![test_2](https://github.com/lewisExternal/graveYardPrivatePublish/assets/81447748/79b1ef83-9704-4fd8-8349-58835d7ddbdb)
![test_3](https://github.com/lewisExternal/graveYardPrivatePublish/assets/81447748/5f392d12-b87c-49fb-81a4-51be13024744)

## Run Locally  

### Data collection and annotation 
Change directory to the data sub directory and run the following. 
```
docker compose up --build 
```

For the streamlit application to collect images, please navigate to:  
```
http://localhost:8501/
```
To see label studio for the annotation of images, please navigate to: 
```
http://localhost:8888/
```
Once finished be sure to run the following.
```
docker compose down
```


### Train model 
Change directory to the training sub directory and run the following.
```
docker compose up --build 
```
To see the training notebook, please navigate to:
```
http://localhost:8888/lab
```
Once finished be sure to run the following.
```
docker compose down
```

## Requirements  
Requires docker desktop 

## References 
* https://kikaben.com/yolov5-transfer-learning-dogs-cats/