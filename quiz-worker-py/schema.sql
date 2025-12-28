DROP TABLE IF EXISTS "comparison";
DROP TABLE IF EXISTS "visit";
DROP TABLE IF EXISTS "pub";
DROP TABLE IF EXISTS "user";

CREATE TABLE "user"(
  "id" INTEGER,
  "username" TEXT,
  "password" TEXT,
  PRIMARY KEY ("id"),
  CONSTRAINT UC_username UNIQUE (username)
);

CREATE TABLE "pub"(
  "id" INTEGER,
  "place_id" TEXT,
  "name" TEXT,
  "frequency" TEXT, -- "weekly" or "monthly"
  "day_of_week" INTEGER, -- Monday is 0 and Sunday is 7
  "time" TEXT, -- must be formatted HH:MM on 24 hours
  "weeks_of_month" TEXT, -- only for "monthly": should be comma-separated 1-4
  "timezone" TEXT, -- format like "Europe/London"
  "address" TEXT,
  "lat" REAL,
  "lng" REAL,
  PRIMARY KEY ("id"),
  CONSTRAINT UC_place_id UNIQUE (place_id)
);

CREATE TABLE "visit"(
  "id" INTEGER,
  "user_id" INTEGER,
  "pub_id" INTEGER,
  "date" TEXT,
  PRIMARY KEY ("id"),
  FOREIGN KEY (user_id) REFERENCES user(id),
  FOREIGN KEY (pub_id) REFERENCES pub(id),
  CONSTRAINT UC_pub_id_date_user_id UNIQUE (pub_id, date, user_id)
);

CREATE TABLE "comparison"(
  "id" INTEGER,
  "visit_id" INTEGER,
  "compare_pub_id" INTEGER,
  "better" INTEGER, -- if null, they haven't been compared yet. if 0, compare_pub_id is better. if 1, visit_id is better.
  PRIMARY KEY ("id"),
  FOREIGN KEY (visit_id) REFERENCES visit(id),
  FOREIGN KEY (compare_pub_id) REFERENCES pub(id),
  CONSTRAINT UC_visit_id_compare_pub_id UNIQUE (visit_id, compare_pub_id)
);

-- DON'T USE THIS PASSWORD IN PRODUCTION!
INSERT INTO user (username, password) VALUES ('suriya', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8');

INSERT INTO pub (place_id, name, frequency, day_of_week, time, timezone, address, lat, lng) VALUES (
  '512c499eebfbe001c0592313f06b24be4a40f00103f9015328b49e02000000c0020192030c4d61636b6965204d61796f72e203246f70656e7374726565746d61703a76656e75653a6e6f64652f3131323532353431353233',
  'Mackie Mayor', 'weekly', 1, "18:00", "Europe/London", 'Mackie Mayor, 1 Eagle Street, Manchester, M4 5BU, United Kingdom', 53.4854865,  -2.2348555
);
INSERT INTO pub (place_id, name, frequency, day_of_week, time, weeks_of_month, timezone, address, lat, lng) VALUES (
  '51a7b79ad07fda01c059805fc88f9dbd4a40f00103f901dd5c7c1501000000c002019203105468652050656e20262050656e63696ce203236f70656e7374726565746d61703a76656e75653a6e6f64652f34363535343339303639',
  'The Pen & Pencil', 'monthly', 2, "19:30", '1,3', "Europe/London", 'The Pen & Pencil, 16 Tariff Street, Manchester, M1 2FN, United Kingdom', 53.4813709, -2.2316891
);

INSERT INTO visit (pub_id, date, user_id) VALUES (1, '2025-01-14', 1);
INSERT INTO visit (pub_id, date, user_id) VALUES (2, '2025-01-11', 1);

INSERT INTO comparison (visit_id, compare_pub_id, better) VALUES (2, 1, 1);

