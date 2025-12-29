### quiz_maps

TODO:
* Edit pub quiz information (including making a quiz inactive - show on ranking but not on upcoming events)
- Add edit button to tooltip and turn into a form.
- Show inactive pubs on a separate page.
* Show number of visits

Site to show pub quiz days and ratings around Manchester.

Method:
* Pick a random quiz (1) that has already been visited by user
* Ask if the new quiz was better or worse than that
* Find one that was better/worse rated already than quiz 1
* Ask if the new quiz was better or worse than that
* Repeat up to 3 times for placement.
* Do not use each visit as a separate one to ask about, but ask if it was better/worse than the previous visit to the same place if repeated. This will allow a quiz to be re-rated by recency. Store the rating of that quiz after each visit.

