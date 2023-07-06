from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import CollectionTable, TopicTable, ItemTable, UserItem, CustomUser
import json
from urllib.parse import urlencode
import time  

def print_success(testname):
    print('==============================================')
    print(f'Test for {testname} passed successfully.')
    print('==============================================')

class FlashcardsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user1 = CustomUser.objects.create_user(
            username="user1",
            password="password",
            realname="User One",
            description="User One description",
            awards="Award1, Award2"
        )
        self.user2 = CustomUser.objects.create_user(
            username="user2",
            password="password",
            realname="User Two",
            description="User Two description",
            awards="Award3, Award4"
        )


    def json_post_req(self, endpoint, data):
        return self.client.post(reverse(endpoint), data=json.dumps(data), content_type='application/json')
    
    def json_get_req(self, endpoint, data = None):
        if data:
            return self.client.get(reverse(endpoint) + '?' + urlencode(data))
        else: 
            return self.client.get(reverse(endpoint)) 

    
    # HELPER FUNCTION: also sets the cookie 
    def login_user_for_tests(self, username, password):    
        # clear existing Authorization header if possible, aka log out
        self.client.credentials(HTTP_AUTHORIZATION='')  # Correct way to clear the credentials

        # login
        response = self.json_post_req('login',{'username': username, 'password': password})
        #response = self.client.post(reverse('login'), data={'username': username, 'password': password})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        # add access token to Authorization header
        token = response.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        # return
        return response 
    

    # 1. (AUTHENTICATION) Simple Registration
    def test_authentication(self):
        print("Testing authentication...")

        response = self.json_post_req('register', {'username': 'testuser', 'password': 'testpass'})
        self.assertEqual(response.status_code, 201)
        print_success("authentication")

    # 2. (PROFILES) Register two users, view own profile, make update, have other person view first profile
    def test_profiles(self):
        print("Testing profiles...")

        # login
        response = self.login_user_for_tests('user1', 'password')
        self.assertEqual(response.json()['status'], 'success')
        
        # view own profile
        response = self.json_get_req('view_profile')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], 'user1')
        
        # update profile
        response = self.json_post_req('edit_profile',{"description": "New description"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['description'], 'New description')
        
        # other person view first profile
        response = self.login_user_for_tests('user2', 'password')
        response = self.json_get_req('view_profile', {'user_id': self.user1.id})
        response = self.client.get(reverse('view_profile', kwargs={'user_id': self.user1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['description'], 'New description')
        print_success("profiles")

    # 3. (DATA SETUP) Register user, make collection, make three topics, add two to collection, remove one from collection, add items. Then check all items in collection
    def test_data_setup(self):
        print("Testing data setup...")

        self.login_user_for_tests('user1', 'password')
        
        # create collection
        response = self.json_post_req('create_collection', {'collection_name': 'Collection1'})
        self.assertEqual(response.status_code, 201)
        collection_id = response.json()['id']
        
        # create three topics, and add 3 + i items to each of them 
        for i in range(3):
            response = self.json_post_req('create_topic',{'topic_name': f'Topic{i + 1}'})
            self.assertEqual(response.status_code, 201)
            topic_id = response.json()['id']
            
            # add items to topic
            items_to_add = [[f'front{j + 1}', f'back{j + 1}'] for j in range(3+i)]
            response = self.json_post_req('add_items_to_topic', {'topic_id': topic_id, 'items': items_to_add})
            self.assertEqual(response.status_code, 200)
            
            if i > 0:
                # add two topics to collection
                response = self.json_post_req('edit_topics_in_collection',{'collection_id': collection_id, 'topic_edits': [[topic_id, 'add']]})
                self.assertEqual(response.status_code, 200)

        # verify number of topics
        response = self.json_get_req('get_all_collections')
        print('\ninitial collections = ', response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(len(response.json()[0]['topics']), 2)
        
        # fetch all items from collection
        response = self.json_get_req('fetch_n_from_collection', {'collection_id': collection_id, 'n': 100})
        self.assertEqual(response.status_code, 200)
        items_count_before = len(response.json())

        # remove one topic from collection
        response = self.json_post_req('edit_topics_in_collection',{'collection_id': collection_id, 'topic_edits': [[topic_id, 'delete']]})
        self.assertEqual(response.status_code, 200)
        
        # verify number of topics
        response = self.json_get_req('get_all_collections')
        print('\nfinal collections = ', response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(len(response.json()[0]['topics']), 1)
        
        # fetch all items from collection
        response = self.json_get_req('fetch_n_from_collection',{'collection_id': collection_id, 'n': 100})
        self.assertEqual(response.status_code, 200)
        items_count_after = len(response.json())

        self.assertLess(items_count_after, items_count_before)
        print_success("data setup")

        
    
    # 4. (STUDYING) Register user, make collection, make two topics, disactivate one, make some items, alternate between fetching n and updating
    # still would want to check for going out of the bounds with the score 
    def test_studying(self):
        print("Testing studying...")
        num_items_total = 5
        fetch_size = 3
        num_fetches = 5

        self.login_user_for_tests('user1', 'password')
        
        # create collection
        response = self.json_post_req('create_collection',{'collection_name': 'Collection1'})
        self.assertEqual(response.status_code, 201)
        collection_id = response.json()['id']
        
        # create two topics
        topic_ids = []
        for i in range(2):
            response = self.json_post_req('create_topic',{'topic_name': f'Topic{i + 1}'})
            self.assertEqual(response.status_code, 201)
            topic_ids.append(response.json()['id'])
            # add two topics to collection
            response = self.json_post_req('edit_topics_in_collection',{'collection_id': collection_id, 'topic_edits': [[response.json()['id'], 'add']]})
            self.assertEqual(response.status_code, 200)
        
        # deactivate one topic
        response = self.json_post_req('edit_topics_in_collection',{'collection_id': collection_id, 'topic_edits': [[topic_ids[0], 'update']]})
        self.assertEqual(response.status_code, 200)

        # create some items
        for i in range(num_items_total):
            response = self.json_post_req('add_items_to_topic',{'topic_id': topic_ids[1], 'items': [[f'front{i + 1}', f'back{i + 1}']]})
            self.assertEqual(response.status_code, 200)

        # alternate between fetching n and updating
        for _ in range(num_fetches):  # change this value as per your requirements
            # fetch 5 items from collection
            response = self.json_get_req('fetch_n_from_collection', {'collection_id': collection_id, 'n': fetch_size})
            self.assertEqual(response.status_code, 200)
            
            items_data = [{'item_id': item['id'], 'increment': 1} for item in response.json()]
            
            # update fetched items
            response = self.json_post_req('update_n_items_user',{'items': items_data})
            self.assertEqual(response.status_code, 200)

        # visualize the final scoring
        response = self.json_get_req('fetch_n_from_collection',{'collection_id': collection_id, 'n': num_items_total})
            
        # some sort of check that the order is correct
        min_fetches = num_fetches*fetch_size // num_items_total
        for item in response.json():
            self.assertLess(min_fetches - 1, item['score']) 
        print('final score list = ', response.json()) # just for visualis
        print_success("studying")




    # what are the tests we want
    # 5. (GLOBAL VIEWING) register three users, make topics with each of them, user 1 wants to view from other two. user 2 sets to global 'view', user 3 sets to private. Then, have uesr3 set to global 'edit', and have user1 try to add items to both 2 and 3's topics. 
    # 6. (FETCH TIMING) register user, set up three topics, add 25 items to one, 400 to another, and 10000 to another. Add each to different collections, and run the fetch_n. See difference in timings. 
    # 7. (TOKENS) register user, try using the update token endpoint, and make sure you can still access edit_profile(self) endpoint


"""
class FlashcardsTestCase1(TestCase):
    def setUp(self):
        self.client = Client()
        #self.user = get_user_model().objects.create_user(username='testuser', password='testpass')

        self.user1 = CustomUser.objects.create_user(
            username="user1",
            password="password",
            realname="User One",
            description="User One description",
            awards="Award1, Award2"
        )
        self.user2 = CustomUser.objects.create_user(
            username="user2",
            password="password",
            realname="User Two",
            description="User Two description",
            awards="Award3, Award4"
        )

    def _check_profile_data(self, data, username):
        #Check that the data includes the public profile data for the given username. 
        expected_user = CustomUser.objects.get(username=username)
        expected_data = {
            "username": expected_user.username,
            "realname": expected_user.realname,
            "description": expected_user.description,
            "awards": expected_user.awards,
            # Add any other public profile fields here
        }
        self.assertEqual(data, expected_data)

    def _check_data_visibility(self, data, expected_visibility):
        #Check that all items in the data have the expected visibility.
        for item in data:
            self.assertEqual(item['visibility'], expected_visibility)

    # registers a user, and then logs in
    def test_login(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('view_profile'))
        self.assertEqual(response.status_code, 200)
        print_success('user login')

    # edits the profile, and then views it
    def test_edit_and_view_profile(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('edit_profile'), {'username': 'newtestuser'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('view_profile'))
        self.assertEqual(response.json()['username'], 'newtestuser')
        print_success('edit and view profile')

    # creates 3 topics, and get_all_topics. Set 1 to global. 
    def test_create_topics_and_view(self):
        self.client.login(username='testuser', password='testpass')
        self.client.post(reverse('create_topic'), {'topicname': 'topic1'}, content_type='application/json')
        self.client.post(reverse('create_topic'), {'topicname': 'topic2'}, content_type='application/json')
        self.client.post(reverse('create_topic'), {'topicname': 'topic3', 'visibility': 'global_view'}, content_type='application/json')
        response = self.client.get(reverse('get_all_topics'))
        self.assertEqual(len(response.json()), 3)
        print_success('create topics and view')

    # create topics, add multiple items to one of the topics, and get_all_items for multiple topics. 
    def test_create_items_and_view(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('create_topic'), {'topicname': 'topic1'}, content_type='application/json')
        topic_id = response.json()['id']
        self.client.post(reverse('add_items_to_topic'), {'topic': topic_id, 'items': [{'front': 'front1', 'back': 'back1'}, {'front': 'front2', 'back': 'back2'}]}, content_type='application/json')
        response = self.client.get(reverse('get_all_items'))
        self.assertEqual(len(response.json()), 2)
        print_success('create items and view')

    # create_collection, create topics, edit_topics_in_collection, get_all_collections
    def test_assemble_collection_and_view(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('create_collection'), {'collection_name': 'collection1'}, content_type='application/json')
        collection_id = response.json()['id']
        response = self.client.post(reverse('create_topic'), {'topicname': 'topic1'}, content_type='application/json')
        topic_id = response.json()['id']
        self.client.post(reverse('edit_topics_in_collection'), {'collection': collection_id, 'topics': [topic_id], 'what': 'add'}, content_type='application/json')
        response = self.client.get(reverse('get_all_collections'))
        self.assertEqual(len(response.json()), 1)
        print_success('assemble collection and view')

    # delete an item from the topic, and view
    def test_delete_from_topic(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('create_topic'), {'topicname': 'topic1'}, content_type='application/json')
        topic_id = response.json()['id']
        response = self.client.post(reverse('add_items_to_topic'), {'topic': topic_id, 'items': [{'front': 'front1', 'back': 'back1'}]}, content_type='application/json')
        item_id = self.client.post(reverse('add_items_to_topic'), content_type='application/json')[0]['id'] #trying to get id of one item
        self.client.post(reverse('delete_items_from_topic'), {'items': [item_id]}, content_type='application/json')
        response = self.client.get(reverse('get_all_items'))
        self.assertEqual(len(response.json()), 0)
        print_success('delete from topic')

    # create topics and some items, do multiple updates, check the return properly reflects the updates, do a fetch, make sure that they come in right order on the fetch
    def test_update_items_check_and_fetch(self):
        # Prepare data
        topic = TopicTable.objects.create(user=self.user1, topicname="topic1")
        items_data = [{'front': f'front{i}', 'back': f'back{i}'} for i in range(5)]
        ItemTable.add_items_to_topic(self.user1, topic.id, items_data)

        # Multiple updates
        user_items = UserItem.objects.filter(user=self.user1)
        increments = [1, 2, -1, 3, -2]
        for user_item, increment in zip(user_items, increments):
            user_item.score += increment
            user_item.save()

        # Fetch
        fetched_items = UserItem.fetch_n_from_user(self.user1, 5)

        # Check order and scores
        expected_scores = [i + 3 for i in increments]  # Initial score is 3 for each item
        for item, expected_score in zip(fetched_items, expected_scores):
            self.assertEqual(item.score, expected_score)
        print_success('update items check and fetch')


    # log in two users, first on create stuff including private and global, then as other user, call view profile, items, topics, collections. make sure only global can be viewed
    def test_view_other_user(self):
        
        # User1 creates items, topics, collections
        self.client.login(username='user1', password='password')
        self._create_sample_data()  # Needs to be updated to use HTTP requests

        # User2 views user1's profile, items, topics, collections
        self.client.login(username='user2', password='password')
        response = self.client.get(reverse('view_profile'), {'username': 'user1'})
        self._check_profile_data(response.json(), 'user1')  # Check that only public data is included

        # Views user1's items, topics, collections
        for view_url in ['get_all_items', 'get_all_topics', 'get_all_collections']:
            response = self.client.get(reverse(view_url), {'username': 'user1'})
            self._check_data_visibility(response.json(), 'global_view')  # Check that only global data is included
        print_success('view other user')



    # FOR LATER, test timing of the fetch, on 3 different topics. You are fetching only the top N=20, 
    # but on topics with size of 25, 200, 1000. This means you will need to add a lot of itesm, but no fear, 
    # add_items_to_topic lets you add all the items at the same time. 
    def test_fetch_timing(self):
        self.client.login(username='user1', password='password')

        # Prepare topics and add items
        items_sizes = [30, 200, 1000]
        for i, items_size in enumerate(items_sizes):
            # Create topic
            response = self.client.post(reverse('create_topic'), {'topicname': f'topic{i+1}'}, content_type='application/json')
            topic_id = response.json()['id']

            # Add items
            for _ in range(items_size // 10):  # Add items 10 at a time
                items_data = [{'front': f'front{j}', 'back': f'back{j}'} for j in range(10)]
                self.client.post(reverse('add_items_to_topic'), {'topic': topic_id, 'items': items_data}, content_type='application/json')

            # Measure time for fetching
            start = time.perf_counter()
            self.client.get(reverse('fetch_n_from_topic'), {'topic': topic_id, 'n': 20})
            elapsed_time = time.perf_counter() - start
            print(f"Time elapsed for fetching from topic {topic_id}: {elapsed_time:.6f} seconds")
        print_success('fetch timing')
    
    # FOR LATER, test token assignment, and token refresh working
    def test_tokens(self):
        # Test the user registration endpoint
        response = self.client.post(reverse('register'), {'username': 'newuser', 'password': 'newpass'}, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.json())

        # Test the user login endpoint
        response = self.client.post(reverse('user_login'), {'username': 'newuser', 'password': 'newpass'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.json())

        # Try to access a protected route without a token
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 403)

        # Try to access a protected route with a token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.json()["access"]}', content_type='application/json')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        print_success('test tokens')

    
    

    
    # ALREADY CREATED TESTS    
    def test_create_collection(self):
        # Log in the test user
        self.client.login(username='testuser', password='testpass')

        # Send a POST request to create a collection. 
        # The request data is a dictionary with a single key 'collection_name'
        response = self.client.post(reverse('create_collection'), 
                                    json.dumps({'collection_name': 'Test Collection'}), 
                                    content_type='application/json')

        # Check that the response has a status code of 201 (created)
        self.assertEqual(response.status_code, 201)

        # Check that one collection object has been created in the database
        self.assertEqual(CollectionTable.objects.count(), 1)

        # Check that the created collection object has the correct name
        self.assertEqual(CollectionTable.objects.get().collection_name, 'Test Collection')
        
        # If everything goes right, print the success message
        print_success('creating a collection')

    def test_create_topic(self):
        # Log in the test user
        self.client.login(username='testuser', password='testpass')

        # Send a POST request to create a topic.
        # The request data is a dictionary with a single key 'topicname'
        response = self.client.post(reverse('create_topic'), 
                                    json.dumps({'topicname': 'Test Topic'}), 
                                    content_type='application/json')

        # Check that the response has a status code of 201 (created)
        self.assertEqual(response.status_code, 201)

        # Check that one topic object has been created in the database
        self.assertEqual(TopicTable.objects.count(), 1)

        # Check that the created topic object has the correct name
        self.assertEqual(TopicTable.objects.get().topicname, 'Test Topic')

        # If everything goes right, print the success message
        print_success('creating a topic')

    def test_add_items_to_topic_and_get_all_items(self):
        # Log in the test user
        self.client.login(username='testuser', password='testpass')

        # Send a POST request to create a topic
        topic_response = self.client.post(reverse('create_topic'), 
                                        json.dumps({'topicname': 'Test Topic'}), 
                                        content_type='application/json')
        
        # Extract the topic id from the response
        topic_id = topic_response.json()['id']

        # Define items to be added
        items = [
            {'front': 'front1', 'back': 'back1'},
            {'front': 'front2', 'back': 'back2'},
        ]

        # Send a POST request to add items to the topic
        # The request data is a dictionary with keys 'topic' (id of the topic) and 'items' (list of items)
        add_items_response = self.client.post(reverse('add_items_to_topic'), 
                                            json.dumps({'topic': topic_id, 'items': items}), 
                                            content_type='application/json')

        # Check that the response has a status code of 200 (OK)
        self.assertEqual(add_items_response.status_code, 200)

        # Check that two item objects have been created in the database
        self.assertEqual(ItemTable.objects.count(), 2)

        # Send a GET request to get all items
        all_items_response = self.client.get(reverse('get_all_items'))

        # Check that the response has a status code of 200 (OK)
        self.assertEqual(all_items_response.status_code, 200)

        # Check that the response contains 2 items
        self.assertEqual(len(all_items_response.json()), 2)

        # If everything goes right, print the success message
        print_success('adding items to topic and getting all items')
"""