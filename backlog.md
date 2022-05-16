# AG_Votes Backlog - Updates to be considered

Here is a list of updates to be considered, and related status.  
If you would like to propose an update, please contact me.  

## To Do

- all companies need to have their own logo (bug on home page for site admin)
- manage models constraints: event name's unicity (per company)
- add comments in .js and .css to identify html pages
- Upgrade Django and take advantage of ASGI (might come with Python and PostgreSQL version upgrades too)
- Integrate JS framework (React?)
- enhance display (colors, blocks, alignments, etc.)
- Add legal mentions - RGPD compliance (+ certifications)
- Closed event should not be modified anymore
- check that the whole list of users, from each group linked to a single event, is unique
  (i.e. a user can be in only one group for a single event)

- Date field: ad date picker
- Implement rules to use or not groups (property at company level already defined)
  (define how to make it compliant with groups + allow or not access to group management + update 'import users' feature accordingly)
- Move event supervision in admin part, to allow admins to vote normally in the vote part (consider renaming each part)
- Add a company property to allow or not a user being part of more than one group  
  (add property in settings + update group management accordingly)
- Use modals to create objects (admin corner + proxy management + mail management)
- Ability to cancel an event (status management)
- Ability to send emails to groups / related to an event
- Access to some admin pages (at least event details) directly from the app (once modal pages are implemented)
- Password management: new password, recovery process, etc.
- consider using django-widget-tweaks module to enhance forms rendering
- Cross company deep tests
- Multi language app
- Define a mobile application

- add a company or event level's choice field to define the label for questions / resolutions. Depending on the event's nature, property to be defined at event's level, default value could be chosen / defined at company's level )

## Done

- (None yet, dev in progress)

## Abandoned

- (None yet, dev in progress)
