"""
filename: controllers.py
description: Controller for Committees.
created by: Omar De La Hoz (oed7416@rit.edu)
created on: 09/19/17
"""

from flask_socketio import emit
from app import socketio, db
from app.committees.models import Committees
from app.users.models import Users

##
## @brief      Gets list of all committees.
##
## @param      broadcast  Flag to broadcast list of committees to all users.
##
## @emit       Emits a list of committees and the committee count.
##
@socketio.on('get_committees')
def get_committees(broadcast = False):
	committees = Committees.query.all()
	comm_ser = [{"id": c.id, "title": c.title} for c in committees]
	emit("get_committees", {"committees": comm_ser, "count": len(committees)}, broadcast= broadcast)
	

##
## @brief      Gets a specific committee by its id.
##
## @param      committee_id  The committee identifier
##
## @emit       Committee Id, Title, Description and Committee Head.
##
@socketio.on('get_committee')
def get_committee(committee_id, broadcast = False):

	committee = Committees.query.filter_by(id = committee_id).first()

	if committee is not None:

		emit("get_committee", {"id": committee.id,
							   "title": committee.title, 
							   "description": committee.description,
							   "location": committee.location,
							   "meeting_time": committee.meeting_time,
							   "head": committee.head})
	else:
		emit('get_committee', {'error', "Committee doesn't exist."})


##
## @brief      Creates a committee. (Must be admin user)
##
## @param      user_data  The user data required to create a committee.
## 			   			  Contains keys 'token', 'title', 
## 			   			  'description' and 'head',
##
## @emit       Emits a success message if created, error if not.
##
@socketio.on('create_committee')
def create_committee(user_data):

	user = Users.verify_auth(user_data["token"])

	if user is not None and user.is_admin:

		# Build committee id string.
		committee_id = user_data["title"].replace(" ", "")
		committee_id = committee_id.lower()

		if Committees.query.filter_by(id = committee_id).first() is None:

			new_committee = Committees(id = committee_id)
			new_committee.title = user_data["title"]
			new_committee.description = user_data["description"]
			new_committee.location = user_data["location"]
			new_committee.meeting_time = user_data["meeting_time"]
			new_committee.head = user_data["head"]

			db.session.add(new_committee)
			db.session.commit()
			emit('create_committee', {'success': 'Committee succesfully created'})
			get_committees(broadcast= True)
		else:
			emit('create_committee', {'error', "Committee already exists."})
	else:
		emit('create_committee', {'error', "User doesn't exist or is not admin."})


##
## @brief      Edits a committee (Must be admin user)
##
## @param      user_data  The user data to edit a committee, must
## 						  contain a token and any of the following
## 						  fields:
## 						  - description
## 						  - head
## 						  - location
## 						  - meeting_time
## 						  
## 						  Any other field will be ignored.
##
## @emit       Emits a success mesage if edited, errors otherwise.
##
@socketio.on('edit_committee')
def edit_committee(user_data):

	user = Users.verify_auth(user_data["token"])

	if user is not None and user.is_admin:

		committee = Committees.query.filter_by(id= user_data["id"]).first()

		if committee is not None:

			for key in user_data:

				if (key == "description" or key == "head" or
				   key == "location" or key == "meeting_time"):

					setattr(committee, key, user_data[key])

			try:
				db.session.commit()

				# Send successful edit notification to user 
				# and broadcast committee changes.
				emit("edit_committee", {"success": "Committee succesfully edited."})
				get_committees(committee.id, broadcast= True)
			except Exception as e:
				db.session.rollback()
				emit("edit_committee", {"error": "Committee couldn't be edited, check data."})
		else:
			emit('edit_committee', {'error', "Committee doesn't exist."})
	else:
		emit('edit_committee', {'error', "User doesn't exist or is not admin."})
