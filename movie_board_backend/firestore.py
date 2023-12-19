import firebase_admin  # type: ignore[]
from firebase_admin import firestore_async  # type: ignore[]

from .configs import PROJECT_ID

admin = firebase_admin.initialize_app(  # type: ignore[]
    credential=firebase_admin.credentials.Certificate("serviceAccountKey.json"),
    options={"databaseURL": f"https://{PROJECT_ID}.firebaseio.com"},
)

db = firestore_async.client()  # type: ignore[]
