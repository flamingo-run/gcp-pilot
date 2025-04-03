# Cloud Pub/Sub

Cloud Pub/Sub is a messaging service for exchanging event data among applications and services. The `CloudPublisher`, `CloudSubscriber`, and `Message` classes in gcp-pilot provide high-level interfaces for interacting with Google Cloud Pub/Sub.

## Installation

To use the Cloud Pub/Sub functionality, you need to install gcp-pilot with the pubsub extra:

```bash
pip install gcp-pilot[pubsub]
```

## Usage

### CloudPublisher

The `CloudPublisher` class allows you to create and manage topics, and publish messages to them.

#### Initialization

```python
from gcp_pilot.pubsub import CloudPublisher

# Initialize with default credentials
publisher = CloudPublisher()

# Initialize with specific project
publisher = CloudPublisher(project_id="my-project")

# Initialize with message ordering enabled
publisher = CloudPublisher(enable_message_ordering=True)

# Initialize with service account impersonation
publisher = CloudPublisher(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

#### Managing Topics

```python
# Create a topic
topic = publisher.create_topic(
    topic_id="my-topic",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    exists_ok=True,  # Optional: if True, returns the existing topic if it already exists
    labels={"environment": "production"},  # Optional: labels to apply to the topic
)
print(f"Topic created: {topic.name}")

# Update a topic
topic = publisher.update_topic(
    topic_id="my-topic",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    labels={"environment": "staging"},  # New labels to apply to the topic
)
print(f"Topic updated: {topic.name}")

# Get a topic
topic = publisher.get_topic(
    topic_id="my-topic",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Topic: {topic.name}")

# List topics
topics = publisher.list_topics(
    prefix="my-",  # Optional: filter topics by prefix
    suffix="-topic",  # Optional: filter topics by suffix
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for topic in topics:
    print(f"Topic: {topic.name}")
```

#### Publishing Messages

```python
# Publish a message to a topic
message_id = publisher.publish(
    message="Hello, world!",
    topic_id="my-topic",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    attributes={"key": "value"},  # Optional: attributes to attach to the message
)
print(f"Message published with ID: {message_id}")

# Publish a message to a topic that doesn't exist yet (it will be created automatically)
message_id = publisher.publish(
    message="Hello, world!",
    topic_id="new-topic",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Message published with ID: {message_id}")
```

### CloudSubscriber

The `CloudSubscriber` class allows you to create and manage subscriptions, and subscribe to messages.

#### Initialization

```python
from gcp_pilot.pubsub import CloudSubscriber

# Initialize with default credentials
subscriber = CloudSubscriber()

# Initialize with specific project
subscriber = CloudSubscriber(project_id="my-project")

# Initialize with service account impersonation
subscriber = CloudSubscriber(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

#### Managing Subscriptions

```python
# Create a subscription
subscription = subscriber.create_subscription(
    topic_id="my-topic",
    subscription_id="my-subscription",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    exists_ok=True,  # Optional: if True, returns the existing subscription if it already exists
    auto_create_topic=True,  # Optional: if True, creates the topic if it doesn't exist
    enable_message_ordering=False,  # Optional: if True, enables message ordering
    push_to_url=None,  # Optional: URL to push messages to
    use_oidc_auth=False,  # Optional: if True, uses OIDC authentication for push
    dead_letter_topic_id=None,  # Optional: topic to send dead-letter messages to
    dead_letter_subscription_id=None,  # Optional: subscription for the dead-letter topic
    max_retries=None,  # Optional: maximum number of delivery attempts
    min_backoff=10,  # Optional: minimum backoff time in seconds
    max_backoff=600,  # Optional: maximum backoff time in seconds
    expiration_ttl=31,  # Optional: expiration time in days
    enable_exactly_once_delivery=False,  # Optional: if True, enables exactly-once delivery
    message_filter=None,  # Optional: filter for messages
)
print(f"Subscription created: {subscription.name}")

# Update a subscription
subscription = subscriber.update_subscription(
    topic_id="my-topic",
    subscription_id="my-subscription",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    push_to_url="https://example.com/push",  # Optional: URL to push messages to
    use_oidc_auth=True,  # Optional: if True, uses OIDC authentication for push
    dead_letter_topic_id="my-dead-letter-topic",  # Optional: topic to send dead-letter messages to
    dead_letter_subscription_id="my-dead-letter-subscription",  # Optional: subscription for the dead-letter topic
    max_retries=5,  # Optional: maximum number of delivery attempts
    min_backoff=30,  # Optional: minimum backoff time in seconds
    max_backoff=300,  # Optional: maximum backoff time in seconds
    expiration_ttl=None,  # Optional: expiration time in days (None means never expire)
    message_filter="attributes.key = \"value\"",  # Optional: filter for messages
)
print(f"Subscription updated: {subscription.name}")

# Create or update a subscription
subscription = subscriber.create_or_update_subscription(
    topic_id="my-topic",
    subscription_id="my-subscription",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    auto_create_topic=True,  # Optional: if True, creates the topic if it doesn't exist
    enable_message_ordering=False,  # Optional: if True, enables message ordering
    push_to_url="https://example.com/push",  # Optional: URL to push messages to
    use_oidc_auth=True,  # Optional: if True, uses OIDC authentication for push
    dead_letter_topic_id="my-dead-letter-topic",  # Optional: topic to send dead-letter messages to
    dead_letter_subscription_id="my-dead-letter-subscription",  # Optional: subscription for the dead-letter topic
    max_retries=5,  # Optional: maximum number of delivery attempts
    min_backoff=30,  # Optional: minimum backoff time in seconds
    max_backoff=300,  # Optional: maximum backoff time in seconds
    expiration_ttl=None,  # Optional: expiration time in days (None means never expire)
    message_filter="attributes.key = \"value\"",  # Optional: filter for messages
)
print(f"Subscription created or updated: {subscription.name}")

# Get a subscription
subscription = subscriber.get_subscription(
    subscription_id="my-subscription",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Subscription: {subscription.name}")

# List subscriptions
subscriptions = subscriber.list_subscriptions(
    prefix="my-",  # Optional: filter subscriptions by prefix
    suffix="-subscription",  # Optional: filter subscriptions by suffix
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for subscription in subscriptions:
    print(f"Subscription: {subscription.name}")

# Delete a subscription
subscriber.delete_subscription(
    subscription_id="my-subscription",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

#### Subscribing to Messages

```python
# Define a callback function to process messages
def process_message(message):
    print(f"Received message: {message.data}")
    print(f"Attributes: {message.attributes}")
    message.ack()  # Acknowledge the message

# Subscribe to a topic
subscriber.subscribe(
    topic_id="my-topic",
    subscription_id="my-subscription",
    callback=process_message,
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

### Message

The `Message` class represents a Pub/Sub message and provides methods for serialization and deserialization.

#### Loading Messages

```python
from gcp_pilot.pubsub import Message
import json

# Load a message from a dictionary
message_dict = {
    "message": {
        "attributes": {"key": "value"},
        "data": "SGVsbG8gQ2xvdWQgUHViL1N1YiEgSGVyZSBpcyBteSBtZXNzYWdlIQ==",  # Base64-encoded "Hello Cloud Pub/Sub! Here is my message!"
        "messageId": "136969346945",
    },
    "subscription": "projects/myproject/subscriptions/mysubscription",
}
message = Message.load(body=message_dict)
print(f"Message ID: {message.id}")
print(f"Message Data: {message.data}")
print(f"Message Attributes: {message.attributes}")
print(f"Subscription: {message.subscription}")

# Load a message from a JSON string
message_json = json.dumps(message_dict)
message = Message.load(body=message_json)
print(f"Message ID: {message.id}")
print(f"Message Data: {message.data}")

# Load a message from bytes
message_bytes = json.dumps(message_dict).encode()
message = Message.load(body=message_bytes)
print(f"Message ID: {message.id}")
print(f"Message Data: {message.data}")

# Load a message with a custom parser
def custom_parser(data):
    return data.upper()

message = Message.load(body=message_dict, parser=custom_parser)
print(f"Message Data: {message.data}")  # Will be uppercase
```

#### Dumping Messages

```python
# Create a message
message = Message(
    id="136969346945",
    data="Hello, world!",
    attributes={"key": "value"},
    subscription="projects/myproject/subscriptions/mysubscription",
)

# Dump the message to a JSON string
message_json = message.dump()
print(f"Message JSON: {message_json}")

# Dump the message with a custom parser
def custom_parser(data):
    return data.upper()

message_json = message.dump(parser=custom_parser)
print(f"Message JSON: {message_json}")  # Data will be uppercase
```

## Error Handling

The Pub/Sub classes handle common errors and convert them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    publisher = CloudPublisher()
    publisher.create_topic(topic_id="my-topic", exists_ok=False)
except exceptions.AlreadyExists:
    print("Topic already exists")

try:
    subscriber = CloudSubscriber()
    subscriber.get_subscription(subscription_id="non-existent-subscription")
except exceptions.NotFound:
    print("Subscription not found")

try:
    subscriber = CloudSubscriber()
    subscriber.create_subscription(
        topic_id="my-topic",
        subscription_id="my-subscription",
        max_retries=5,
        dead_letter_topic_id=None,
    )
except exceptions.ValidationError:
    print("max_retries requires dead_letter_topic_id")
```

## Working with Service Account Impersonation

Service account impersonation allows you to act as a service account without having its key file. This is a more secure approach than downloading and storing service account keys.

```python
# Initialize with service account impersonation
publisher = CloudPublisher(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
subscriber = CloudSubscriber(impersonate_account="service-account@project-id.iam.gserviceaccount.com")

# Now all operations will be performed as the impersonated service account
publisher.create_topic(topic_id="my-topic")
subscriber.create_subscription(topic_id="my-topic", subscription_id="my-subscription")
```

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

## Message Filtering

Pub/Sub allows you to filter messages based on their attributes. You can specify a filter when creating or updating a subscription:

```python
# Create a subscription with a filter
subscription = subscriber.create_subscription(
    topic_id="my-topic",
    subscription_id="my-subscription",
    message_filter="attributes.key = \"value\"",
)

# Update a subscription with a filter
subscription = subscriber.update_subscription(
    topic_id="my-topic",
    subscription_id="my-subscription",
    message_filter="attributes.key = \"value\"",
)
```

The filter is a CEL (Common Expression Language) expression that evaluates to a boolean value. For more information on message filtering, see the [Google Cloud Pub/Sub documentation](https://cloud.google.com/pubsub/docs/filtering).

## Dead Letter Topics

Dead letter topics are used to store messages that could not be delivered to a subscription. You can specify a dead letter topic when creating or updating a subscription:

```python
# Create a subscription with a dead letter topic
subscription = subscriber.create_subscription(
    topic_id="my-topic",
    subscription_id="my-subscription",
    dead_letter_topic_id="my-dead-letter-topic",
    dead_letter_subscription_id="my-dead-letter-subscription",
    max_retries=5,
)

# Update a subscription with a dead letter topic
subscription = subscriber.update_subscription(
    topic_id="my-topic",
    subscription_id="my-subscription",
    dead_letter_topic_id="my-dead-letter-topic",
    dead_letter_subscription_id="my-dead-letter-subscription",
    max_retries=5,
)
```

## Push Subscriptions

Pub/Sub supports push subscriptions, which push messages to a webhook endpoint instead of requiring the client to pull messages. You can create a push subscription by specifying a `push_to_url`:

```python
# Create a push subscription
subscription = subscriber.create_subscription(
    topic_id="my-topic",
    subscription_id="my-push-subscription",
    push_to_url="https://example.com/push",
    use_oidc_auth=True,  # Optional: if True, uses OIDC authentication for push
)

# Update a subscription to use push
subscription = subscriber.update_subscription(
    topic_id="my-topic",
    subscription_id="my-subscription",
    push_to_url="https://example.com/push",
    use_oidc_auth=True,
)
```

When using push subscriptions, Pub/Sub will send messages to the specified URL as HTTP POST requests. The message will be in the request body in the format expected by the `Message.load` method.

## Exactly-Once Delivery

Pub/Sub supports exactly-once delivery, which ensures that each message is delivered exactly once to a subscription. You can enable exactly-once delivery when creating a subscription:

```python
# Create a subscription with exactly-once delivery
subscription = subscriber.create_subscription(
    topic_id="my-topic",
    subscription_id="my-subscription",
    enable_exactly_once_delivery=True,
)
```

Note that exactly-once delivery is only supported for push subscriptions that use OIDC authentication.
