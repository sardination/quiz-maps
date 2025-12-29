INSERT INTO pub (place_id, name, frequency, day_of_week, time, timezone, address, lat, lng) VALUES (
  '512c499eebfbe001c0592313f06b24be4a40f00103f9015328b49e02000000c0020192030c4d61636b6965204d61796f72e203246f70656e7374726565746d61703a76656e75653a6e6f64652f3131323532353431353233',
  'Mackie Mayor', 'weekly', 1, "18:00", "Europe/London", 'Mackie Mayor, 1 Eagle Street, Manchester, M4 5BU, United Kingdom', 53.4854865,  -2.2348555
);
INSERT INTO pub (place_id, name, frequency, day_of_week, time, weeks_of_month, timezone, address, lat, lng) VALUES (
  '51a7b79ad07fda01c059805fc88f9dbd4a40f00103f901dd5c7c1501000000c002019203105468652050656e20262050656e63696ce203236f70656e7374726565746d61703a76656e75653a6e6f64652f34363535343339303639',
  'The Pen & Pencil', 'specific-weeks', 2, "19:30", '1,3', "Europe/London", 'The Pen & Pencil, 16 Tariff Street, Manchester, M1 2FN, United Kingdom', 53.4813709, -2.2316891
);

INSERT INTO visit (pub_id, date, user_id) VALUES (1, '2025-01-14', 1);
INSERT INTO visit (pub_id, date, user_id) VALUES (2, '2025-01-11', 1);

INSERT INTO comparison (visit_id, compare_pub_id, better) VALUES (2, 1, 1);