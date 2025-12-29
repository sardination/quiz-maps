-- 01 Init schema

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
  "frequency" TEXT, -- "weekly" or "specific-weeks"
  "day_of_week" INTEGER, -- Monday is 0 and Sunday is 7
  "time" TEXT, -- must be formatted HH:MM on 24 hours
  "weeks_of_month" TEXT, -- only for "specific-weeks": should be comma-separated 1-4
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

