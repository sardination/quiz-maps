from datetime import datetime
from pyodide.ffi import JsNull

def INDEX_TEMPLATE(
    logged_in_user_id,
    all_pubs,
    pub_ranking,
    upcoming_events,
    all_cities,
    geoapify_key=None
):
    # TODO: pin colors based on days

    all_pubs_dict = {
        pub.id: pub
        for pub in all_pubs
    }

    pan_a_tag = lambda pub_id, content: f'<a class="pantag" href="#" onclick="focusPin({pub_id})">{content}</a>'

    ranked_pubs = ',\n'.join([
        f"""
        {{
            lat: {all_pubs_dict[pub_info['id']].lat},
            lng: {all_pubs_dict[pub_info['id']].lng},
            score: {int(pub_info['score'] * 100)},
            num_visits: {pub_info['visits']},
            a_tag: `{pan_a_tag(pub_info['id'], all_pubs_dict[pub_info['id']].name)}`
        }}
        """
        for i, pub_info in enumerate(pub_ranking)
    ])

    unranked_pub_ids = set([pub.id for pub in all_pubs]) - set([pub_info['id'] for pub_info in pub_ranking])
    unranked_pubs = ',\n'.join([
        f"""
        {{
            lat: {all_pubs_dict[pub_id].lat},
            lng: {all_pubs_dict[pub_id].lng},
            a_tag: `{pan_a_tag(pub_id, all_pubs_dict[pub_id].name)}`
        }}
        """
        for pub_id in unranked_pub_ids
    ])

    upcoming_event_items = ',\n'.join([
        f"""
        {{
            lat: {pub.lat},
            lng: {pub.lng},
            event_date: "{event_dt.strftime("%A, %B %d")}",
            a_tag: `{pan_a_tag(pub.id, pub.name)}`,
            event_time: "{event_dt.strftime("%I:%M %p")}"
        }}
        """
        for pub, event_dt in upcoming_events
    ])

    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
    week_ordinals = ["", "1st", "2nd", "3rd", "4th"]

    def get_js_weeks_of_month_str(pub):
        weeks_of_month = [
            week_ordinals[int(wom)]
            for wom in (
                [] if type(pub.weeks_of_month) == JsNull or pub.weeks_of_month == '' else pub.weeks_of_month.split(',')
            )
        ]
        weeks_of_month_str = ""
        if len(weeks_of_month) > 1:
            weeks_of_month_str = ', '.join(weeks_of_month[:-1])
            sep_comma = ',' if len(weeks_of_month) > 2 else ''
            weeks_of_month_str = f"{weeks_of_month_str}{sep_comma} and {weeks_of_month[-1]}"
        elif len(weeks_of_month) == 1:
            weeks_of_month_str = weeks_of_month[0]

        return weeks_of_month_str

    locations = ',\n'.join([
        f"""
        {{
            id: {pub.id},
            place_id: "{pub.place_id}",
            name: "{pub.name}",
            address: "{pub.address}",
            lat: {pub.lat},
            lng: {pub.lng},
            city: "{pub.city}",
            time: "{datetime.strptime(pub.time, "%H:%M").strftime("%I:%M%p")}",
            raw_time: "{pub.time}",
            frequency: "{pub.frequency}",
            day_of_week: "{days_of_week[pub.day_of_week]}",
            weeks_of_month: "{get_js_weeks_of_month_str(pub)}",
            active: {pub.active}
        }}
        """
        for pub in all_pubs
    ])

    cities = ',\n'.join([
        f"""
        {{
            city: "{city.city}",
            min_lat: {city.min_lat},
            min_lng: {city.min_lng},
            max_lat: {city.max_lat},
            max_lng: {city.max_lng},
        }}
        """
        for city in all_cities
    ])

    login_href = '/profile' if logged_in_user_id is not None else '/login'
    login_icon = '🌞' if logged_in_user_id is not None else '🌚'

    add_pub_to_db = ""
    if logged_in_user_id is not None:
        add_pub_to_db = f"""
        // Geoapify for geocoding
        const geoapifyApiKey = "{geoapify_key}";

        // The location that is currently being edited
        var currentEditLoc = null;

        // Function to add location to database
        async function addToDatabase() {{
            const pub_id = currentEditLoc.id;
            const edit = pub_id !== undefined;

            const place_id = currentEditLoc.place_id;
            const address = currentEditLoc.formatted;
            const timezone = edit ? currentEditLoc.timezone : currentEditLoc.timezone.name;
            const lat = currentEditLoc.lat;
            const lng = edit ? currentEditLoc.lng : currentEditLoc.lon;
            const city = currentEditLoc.city

            // TODO: prevent double-submit
            const formId = `form-${{place_id}}`;
            const form = document.getElementById(formId);
            const formData = new FormData(form);

            const scheduleData = {{
                place_id: place_id,
                name: formData.get('name'),
                address: address,
                frequency: formData.get('frequency'),
                dayOfWeek: formData.get('dayOfWeek'),
                weeksOfMonth: formData.getAll('weekOfMonth'),
                time: formData.get('time'),
                timezone: timezone,
                lat: lat,
                lng: lng,
                city: city,
                active: formData.get('active') == '1' ? 1 : 0
            }};

            if (edit) {{
                scheduleData.id = pub_id;
            }}

            // Send POST request
            const response = await fetch('/api/pub', {{
                method: edit ? 'PUT' : 'POST',
                headers: {{
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify(scheduleData)
            }});

            // TODO: instead of reloading, remove popup, add location to pins, and re-zoom map
            window.location.reload();
        }}

        function updateFormFields(formId) {{
            const form = document.getElementById(formId);
            const frequency = form.querySelector('[name="frequency"]').value;
            const weekOfMonthGroup = form.querySelector('.week-of-month-group');

            if (frequency === 'specific-weeks') {{
                weekOfMonthGroup.style.display = 'block';
            }} else {{
                weekOfMonthGroup.style.display = 'none';
            }}
        }}

        function editPub(locId) {{
            const location = locations.filter((loc) => loc.id == locId)[0]
            const marker = map._layers[locIdMap.get(locId)];

            // Remove the info popup and bind the form
            const popupContent = getPubFormPopup(location, true);
            marker.closePopup()
                  .unbindPopup()
                  .bindPopup(popupContent)
                  .openPopup();

            // If the form is closed, then unbind the form popup and bind the info popup again
            marker.getPopup()
                  .on('remove', function () {{
                    marker.unbindPopup()
                          .bindPopup(getInfoPopup(location))
                    currentEditLoc = null;
                  }})
        }}

        function getPubFormPopup(loc, edit) {{
            console.log(loc);
            currentEditLoc = loc;

            const formId = `form-${{loc.place_id}}`;

            const locName = loc.name === undefined ? '' : loc.name;
            const formattedAddress = edit ? loc.address : loc.formatted;

            const weekOfMonthCheckedMap = new Map();
            for (var i=1; i <= 4; i++) {{
                weekOfMonthCheckedMap.set(i, '');
            }}
            if (edit) {{
                for (var i=0; i < loc.weeks_of_month.length; i++) {{
                    weekOfMonthCheckedMap.set(parseInt(loc.weeks_of_month[i].substring(0,1)), 'checked');
                }}
            }}

            var timeValue = "19:00";
            if (edit) {{
                timeValue = loc.raw_time;
            }}

            // TODO: fill form with existing info and update button if quiz already exists
            const popupContent = `
                <div>
                    ${{formattedAddress}}<br><br>

                    <form id="${{formId}}">
                        <label>Name:</label><br>
                        <input
                            type="text" name="name" value="${{locName}}"
                            required placeholder="Enter name"
                            oninvalid="this.setCustomValidity('Enter pub quiz name here')"
                            oninput="this.setCustomValidity('')"
                            style="width: 100%; margin-bottom: 10px;"
                        ><br>

                        <label>Frequency:</label><br>
                        <select name="frequency" onchange="updateFormFields('${{formId}}')" style="width: 100%; margin-bottom: 10px;">
                            <option value="weekly" ${{ edit && loc.frequency == 'weekly' ? 'selected' : ''}}>Every week</option>
                            <option value="specific-weeks" ${{ edit && loc.frequency == 'specific-weeks' ? 'selected' : ''}}>Specific weeks of month</option>
                        </select><br>

                        <div class="week-of-month-group" style="display: ${{ edit && loc.frequency == 'specific-weeks' ? 'block' : 'none'}}; margin-bottom: 10px;">
                            <label>Week(s) of month:</label><br>
                            <label><input type="checkbox" name="weekOfMonth" value="1" ${{weekOfMonthCheckedMap.get(1)}}> 1st</label>
                            <label><input type="checkbox" name="weekOfMonth" value="2" ${{weekOfMonthCheckedMap.get(2)}}> 2nd</label>
                            <label><input type="checkbox" name="weekOfMonth" value="3" ${{weekOfMonthCheckedMap.get(3)}}> 3rd</label>
                            <label><input type="checkbox" name="weekOfMonth" value="4" ${{weekOfMonthCheckedMap.get(4)}}> 4th</label><br>
                        </div>

                        <label>Day of week:</label><br>
                        <select name="dayOfWeek" style="width: 100%; margin-bottom: 10px;">
                            <option value="0" ${{loc.day_of_week == 'Monday' ? 'selected' : ''}}>Monday</option>
                            <option value="1" ${{loc.day_of_week == 'Tuesday' ? 'selected' : ''}}>Tuesday</option>
                            <option value="2" ${{loc.day_of_week == 'Wednesday' ? 'selected' : ''}}>Wednesday</option>
                            <option value="3" ${{loc.day_of_week == 'Thursday' ? 'selected' : ''}}>Thursday</option>
                            <option value="4" ${{loc.day_of_week == 'Friday' ? 'selected' : ''}}>Friday</option>
                            <option value="5" ${{loc.day_of_week == 'Saturday' ? 'selected' : ''}}>Saturday</option>
                            <option value="6" ${{loc.day_of_week == 'Sunday' ? 'selected' : ''}}>Sunday</option>
                        </select><br>

                        <label>Time:</label><br>
                        <input type="time" name="time" value="${{timeValue}}" style="width: 100%; margin-bottom: 10px;"><br>

                        <label>Active?</label>
                        <input type="checkbox" name="active" value="1" ${{loc.active != 0 ? 'checked' : ''}}><br>

                        <br>

                        <button type="button" onclick="addToDatabase()">${{edit ? 'Update' : 'Add'}}</button>
                    </form>
                </div>
            `;

            return popupContent;
        }}

        // Add Geoapify Address Search control
        const addressSearchControl = L.control.addressSearch(geoapifyApiKey, {{
          position: 'topleft',
          resultCallback: (loc) => {{
            map.setView([loc.lat, loc.lon], 25);

            const popupContent = getPubFormPopup(loc, false)

            const marker = L.marker([loc.lat, loc.lon])
                .addTo(map)
                .bindPopup(popupContent)
                .openPopup();

            // If the popup is closed, remove the pin and set editing loc to null.
            marker.getPopup()
                  .on('remove', function () {{
                    marker.remove();
                    currentEditLoc = null;
                  }})
          }},
          suggestionsCallback: (suggestions) => {{
            // console.log(suggestions);
          }}
        }});
        map.addControl(addressSearchControl);
        """

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pub Quiz Map</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <link rel="stylesheet" href="https://unpkg.com/@geoapify/leaflet-address-search-plugin@^1/dist/L.Control.GeoapifyAddressSearch.min.css" />
        <script src="https://unpkg.com/@geoapify/leaflet-address-search-plugin@^1/dist/L.Control.GeoapifyAddressSearch.min.js"></script>
        <link rel="stylesheet" href="https://unpkg.com/leaflet-search@3.0.9/dist/leaflet-search.min.css" />
        <script src="https://unpkg.com/leaflet-search@3.0.9/dist/leaflet-search.min.js"></script>
        <link href="https://ajax.googleapis.com/ajax/libs/jqueryui/1.12.1/themes/base/jquery-ui.css" rel="stylesheet" type="text/css"/>
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js"></script>
        <script src="https://ajax.googleapis.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.js"></script>
        <style>
          .circle-btn {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            border: solid;
            border-color: #000000;
            background-color: #ffffff;
            color: white;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s;
          }}

          .circle-btn:hover {{
            transform: scale(1.1);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
          }}

          .circle-btn:active {{
            transform: scale(0.95);
          }}

          a.pantag:link {{
            color:blue
          }}

          a.pantag:visited {{
            color: blue;
          }}

          .ui-autocomplete {{
            cursor:pointer;
            height:120px;
            overflow-y:scroll;
          }}
        </style>
    </head>
    <body>
        <div style="display: flex; height: 100vh; margin: 0;">
            <div style="flex: 1;">
                <div id="map" style="width: 100%; height: 100%;"></div>
            </div>

            <div style="flex: 1; padding: 20px; overflow-y: auto;">
                <div>
                    <p>Select a city or "ALL" to filter the map, or zoom on the map to set your own bounds</p>
                    <input type="text" id="cityDropdown" placeholder="Pick a city" value="Manchester" />
                </div>

                <div style="margin-bottom: 40px;">
                    <h2>Upcoming Events (Next 7 Days)</h2>
                    <ul id="events-list">

                    </ul>
                </div>

                <div>
                    <h2>Best Quiz Ranking</h2>
                    <table border="1" cellpadding="8" cellspacing="0">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Name</th>
                                <th>Score</th>
                                <th>Visits</th>
                            </tr>
                        </thead>
                        <tbody id="leaderboardBody">

                        </tbody>
                    </table>
                </div>
            </div>
            <button class="circle-btn" onclick="window.location.href='{login_href}';">{login_icon}</button>
        </div>
</body>
        <script>
            // Event and ranking info
            const rankedPubs = [
                {ranked_pubs}
            ];
            const unrankedPubs = [
                {unranked_pubs}
            ];
            const eventItems = [
                {upcoming_event_items}
            ];

            function pubInBounds(bounds, pubLat, pubLng) {{
                const minLat = bounds[0][0];
                const minLng = bounds[0][1];
                const maxLat = bounds[1][0];
                const maxLng = bounds[1][1];

                return pubLat >= minLat && pubLat <= maxLat && pubLng >= minLng && pubLng <= maxLng;
            }}

            function setLeaderboard() {{
                const bounds = getMapBounds();
                const showRankedPubs = rankedPubs.filter(
                    pub => pubInBounds(bounds, pub.lat, pub.lng)
                );
                const showUnrankedPubs = unrankedPubs.filter(
                    pub => pubInBounds(bounds, pub.lat, pub.lng)
                );

                const tbodyElement = $('#leaderboardBody');

                tbodyElement.empty();

                for (var i=0; i < showRankedPubs.length; i++) {{
                    const pub = showRankedPubs[i];
                    const newRow = `<tr>
                        <td>${{i+1}}</td>
                        <td>${{pub.a_tag}}</td>
                        <td>${{pub.score}}</td>
                        <td>${{pub.num_visits}}</td>
                    </tr>`
                    tbodyElement.append(newRow);
                }}

                for (var i=0; i < showUnrankedPubs.length; i++) {{
                    const pub = showUnrankedPubs[i];
                    const newRow = `<tr>
                        <td>-</td>
                        <td>${{pub.a_tag}}</td>
                        <td>-</td>
                        <td>-</td>
                    </tr>`
                    tbodyElement.append(newRow);
                }}
            }}

            function setUpcomingEvents() {{
                $('#events-list').empty();

                const bounds = getMapBounds();
                const showEventItems = eventItems.filter(event => pubInBounds(bounds, event.lat, event.lng));
                for (var i=0; i < showEventItems.length; i++) {{
                    const event = showEventItems[i];
                    const newItem = `<li>${{event.event_date}} - ${{event.a_tag}} @ ${{event.event_time}}</li>`;
                    $('#events-list').append(newItem);
                }}
            }}

            function getInfoPopup(loc) {{
                const freq = loc.frequency == 'weekly' ? `${{loc.day_of_week}}s` : `the ${{loc.weeks_of_month}} ${{loc.day_of_week}} of the month`

                return `
                    <h4>${{loc.name}}${{loc.active == 0 ? ' <strong>(INACTIVE)</strong>' : ''}}</h4>
                    <p>${{loc.address}}</p>
                    <p>${{loc.time}} on ${{freq}}</p>
                    {'<button onclick="editPub(${loc.id})">Edit</button>' if logged_in_user_id is not None else ''}
                `
            }}

            // Pub locations
            const locations = [
                {locations}
            ];

            // Pub cities
            const lats = locations.map(loc => loc.lat);
            const lngs = locations.map(loc => loc.lng);

            const cities = [
                {cities},
                {{city: 'ALL', min_lat: Math.min(...lats), min_lng: Math.min(...lngs), max_lat: Math.max(...lats), max_lng: Math.max(...lngs)}}
            ];

            // Initialize the map to Manchester
            const initCity = 'Manchester';
            const map = L.map('map', {{zoomControl: false}}).setView([53.483959, -2.244644], 14);

            function getMapBounds() {{
                return [
                    [map.getBounds().getSouth(), map.getBounds().getWest()],
                    [map.getBounds().getNorth(), map.getBounds().getEast()]
                ];
            }}

            function getCityInfo(city) {{
                var cityInfo;
                for (var i=0; i < cities.length; i++) {{
                    cityInfo = cities[i];
                    if (cityInfo.city === city) break;
                }}
                return cityInfo;
            }}

            function zoomToCity(city) {{
                const cityInfo = getCityInfo(city);
                map.fitBounds([
                    [cityInfo.min_lat, cityInfo.min_lng],
                    [cityInfo.max_lat, cityInfo.max_lng]
                ], {{ padding: [50, 50] }});
            }}

            zoomToCity(initCity);

            // Add OpenStreetMap tiles
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);

            // Add markers to the map
            var markerLayer = L.layerGroup().addTo(map);
            var locIdMap = new Map();
            locations.forEach(loc => {{
                var marker = L.marker([loc.lat, loc.lng], {{title: loc.name, opacity: loc.active == 0 ? 0.5 : 1}})
                    .addTo(map)
                    .bindPopup(getInfoPopup(loc));
                markerLayer.addLayer(marker);

                locIdMap.set(loc.id, marker._leaflet_id);
            }});

            {add_pub_to_db}

            map.addControl(new L.Control.Search({{
                initial: false,
                layer: markerLayer,
                autoType: false,
                marker: false,
                moveToLocation: (ll, t, m) => {{ll.layer.openPopup()}}
            }}));

            L.control.zoom({{ position: 'bottomright' }}).addTo(map);

            // Focus pin
            function focusPin(locId) {{
                var marker = map._layers[locIdMap.get(locId)];
                map.panTo(marker._latlng);
                marker.openPopup();
            }}

            // Get map bounds
            var currentBounds = null;
            map.on('moveend', function(e) {{
                const newBounds = getMapBounds();
                if (currentBounds != null && newBounds != currentBounds) {{
                    $('#cityDropdown').val('Custom Location');
                }}
                currentBounds = newBounds;
                setLeaderboard();
                setUpcomingEvents();
            }})

            // Populate city dropdown
            $(document).ready(function() {{
                $('#cityDropdown').autocomplete({{
                    source: cities.map(c => c.city),
                    minLength: 0,
                    scroll: true,
                    select: function(event, ui) {{
                        currentBounds = null;
                        zoomToCity(ui.item.value);
                    }}
                }}).on('focus', function () {{
                  $(this).autocomplete('search', '');
                }});
            }});
        </script>

    </html>
    """

