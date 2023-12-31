# MemoryCenter-backend
flashcard-centered application for accelerating and maintaining the consolidation of information in the human brain

## Specifics
Backend uses sqlite for development, simple to transfer to postgress for deployment. 

We split up the normal settings.py into a settings folder that dynamically loads variables based on your DJANGO_ENV

The database is organized in terms of Users, Collections, Topics, and Items. There are some links between them. In short, Users can create and view collections, topics, and items, if they have the proper authentication level. Collections contain topics, and topics contain items. Topics can be in multiple collections, or none, while items can only be in one topic. 


# Setup
1) copy .env.template to .env, and set the environment variables. 
    
    1a. you can generate a secret key using gen_secret_key.py
2) change constants for (game mechanics, access tokens, storage limits, etc) if you'd like, currently sprinkled throughout base.py and views.py and serializers.py (sorry!)
3) if you want to properly implement CORS, need to do manually in the production.py file. you do need to make sure you edit the allowed hosts with the frontend (base.py)
4) normal django init migrations and runserver