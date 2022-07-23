CREATE FUNCTION random_first_name()
  RETURNS text
AS $$
    select (
        array[
            'Aaliyah','Abagail','Abbey','Abbie','Abbigail','Abby','Abigail','Abigale','Abigayle','Abril','Achsah','Ada','Adah','Adaline','Adalyn','Adalynn','Adamaris','Adda','Addie','Addison',
            'Addisyn','Addyson','Adel','Adela','Adelaide','Adele','Adelia','Adelina','Adeline','Adell','Adella','Adelle','Adelyn','Adelynn','Adilene','Adina','Adison','Adline','Adria','Adriana','Adriane',
            'Adrianna','Adrianne','Adriene','Adrienne',
            'Adyson','Affie','Afton','Agatha','Aggie','Agnes','Agness','Agusta','Aida','Aileen',
            'Ailene','Aili','Aimee','Ainsley','Aisha','Aiyana','Aiyanna','Aja','Akeelah','Akira','Ala','Alabama','Alaina','Alana','Alani','Alanna','Alannah','Alaya',
            'Alayna','Alba','Alberta','Albertha','Albertina','Albertine','Albina','Alcie','Alda','Aldona','Aleah','Alease','Alecia','Aleen','Aleena','Alejandra','Alena','Alene','Alesha','Alesia','Alessandra','Aleta','Aletha','Alethea','Alex','Alexa','Alexandr','Alexandra','Alexandrea','Alexandria','Alexia','Alexina','Alexis','Alexus','Alexys','Alfreda','Alia','Aliana','Alice','Alicia','Alida','Alina','Aline','Alisa','Alisha','Alison',        'Aaden','Aarav','Aaron','Ab','Abb','Abbott','Abdiel','Abdul','Abdullah','Abe','Abel','Abelardo','Abie','Abner','Abraham','Abram','Ace','Acey','Acie','Acy','Adalberto','Adam','Adams','Adan','Add','Adelard','Adelbert','Aden','Adin','Aditya','Adlai','Admiral','Adolf','Adolfo','Adolph','Adolphus','Adonis','Adrain','Adrian','Adriel','Adrien','Adron','Aedan','Agustin','Agustus','Ah',
            'Ahmad','Ahmed','Aidan','Aiden','Aidyn','Aime','Akeem','Al','Alan','Alanzo','Albert','Alberto','Albertus',
            'Albin','Albion','Alby','Alcee','Alcide','Alden','Aldo','Alec','Aleck','Alejandro','Alek','Alessandro','Alex','Alexande','Alexander',
            'Alexandre','Alexandro','Alexis','Alexzander','Alf','Alferd','Alfie',
            'Alfonse','Alfonso','Alfonzo','Alford','Alfred','Alfredo','Alger','Algernon','Algie','Algot',
            'Ali','Alijah','Allan','Allen','Allyn','Almer','Almon','Almond','Almus','Alois','Alonso','Alonza','Alonzo','Aloys',
            'Aloysius','Alpheus', 'Alphons','Alphonse','Alphonso','Alphonsus','Alston','Alto','Alton'
        ]
    )[floor(random() * 233 + 1)];
$$ LANGUAGE SQL;


CREATE FUNCTION random_last_name()
  RETURNS text
AS $$
    select (
        array[
            'Abbott','Abernathy','Abshire','Adams','Altenwerth','Anderson','Ankunding',
            'Armstrong','Auer','Aufderhar','Bahringer','Bailey','Balistreri','Barrows','Bartell','Bartoletti','Barton','Bashirian','Batz','Bauch','Baumbach','Bayer','Beahan','Beatty','Bechtelar','Becker','Bednar','Beer','Beier','Berge','Bergnaum','Bergstrom','Bernhard','Bernier','Bins',
            'Blanda','Blick','Block','Bode','Boehm','Bogan','Bogisich',
            'Borer','Bosco','Botsford','Boyer','Boyle','Bradtke','Brakus','Braun','Breitenberg','Brekke','Brown','Bruen','Buckridge',
            'Carroll','Carter','Cartwright','Casper','Cassin','Champlin','Christiansen','Cole','Collier','Collins','Conn','Connelly','Conroy','Considine','Corkery','Cormier','Corwin','Cremin','Crist','Crona','Cronin','Crooks',
            'Cruickshank','Cummerata','Cummings','Dach','Daniel','Dare','Daugherty','Davis','Deckow','Denesik','Dibbert','Dickens','Dicki','Dickinson','Dietrich','Donnelly','Dooley','Douglas','Doyle',
            'DuBuque',  'Durgan',  'Ebert',  'Effertz',  'Eichmann',  'Emard',  'Emmerich',  'Erdman',  'Ernser',  'Fadel',  'Fahey',  'Farrell',  'Fay',  'Feeney',  'Feest',  'Feil',  'Ferry',  'Fisher',
            'Flatley','Frami','Franecki','Friesen','Fritsch','Funk','Gaylord','Gerhold','Gerlach','Gibson','Gislason','Gleason','Gleichner','Glover','Goldner','Goodwin','Gorczany','Gottlieb','Goyette','Grady','Graham','Grant','Green','Greenfelder','Greenholt','Grimes','Gulgowski','Gusikowski','Gutkowski','Gutmann','Haag','Hackett','Hagenes','Hahn','Haley','Halvorson','Hamill',
            'Jacobi','Jacobs','Jacobson','Jakubowski','Jaskolski','Jast','Jenkins','Jerde','Johns','Johnson','Johnston','Jones','Kassulke','Kautzer','Keebler','Keeling','Kemmer','Kerluke','Kertzmann','Kessler','Kiehn','Kihn','Kilback','King',
            'Kirlin','Klein','Kling','Klocko','Koch','Koelpin','Koepp','Kohler','Konopelski','Koss','Kovacek','Kozey','Krajcik','Kreiger','Kris','Kshlerin','Kub','Kuhic','Kuhlman','Kuhn','Kulas',        'Kunde',
            'Kunze','Kuphal','Kutch','Kuvalis','Labadie','Lakin','Lang','Langosh','Langworth','Larkin','Larson','Leannon','Lebsack','Ledner','Leffler','Legros','Lehner','Lemke','Lesch','Leuschke','Lind','Lindgren','Littel','Little','Lockman','Lowe','Lubowitz','Lueilwitz',
            'Luettgen','Lynch','Macejkovic','Maggio','Mann','Mante','Marks','Marquardt','Marvin','Mayer','Mayert','McClure','McCullough','McDermott','McGlynn','McKenzie','McLaughlin','Medhurst','Mertz','Metz','Miller','Mills','Mitchell','Moen','Mohr',
            'Schmitt','Schneider','Schoen','Schowalter','Schroeder','Schulist','Schultz','Schumm','Schuppe','Schuster','Senger','Shanahan','Shields','Simonis','Sipes','Skiles','Smith','Smitham','Spencer','Spinka','Sporer','Stamm','Stanton','Stark','Stehr','Steuber','Stiedemann','Stokes','Stoltenberg','Stracke','Streich','Stroman','Strosin','Swaniawski','Swift','Terry','Thiel','Thompson','Tillman',
            'Torp','Torphy','Towne','Toy','Trantow','Tremblay','Treutel','Tromp','Turcotte','Turner','Ullrich','Upton','Vandervort','Veum','Volkman','Von','VonRueden','Waelchi','Walker','Walsh','Walter','Ward','Waters','Watsica','Weber','Wehner','Weimann','Weissnat','Welch','West','White','Wiegand','Wilderman','Wilkinson','Will','Williamson','Willms','Windler','Wintheiser','Wisoky','Wisozk','Witting','Wiza','Wolf','Wolff','Wuckert','Wunsch','Wyman',
            'Yost','Yundt','Zboncak','Zemlak','Ziemann','Zieme','Zulauf'
        ]
    )[floor(random() * 344 + 1)];
$$ LANGUAGE SQL;



CREATE FUNCTION random_email()
  RETURNS text
AS $$
    SELECT md5(random()::text || clock_timestamp()::text)::text || '@fake.com';
$$ LANGUAGE SQL;


CREATE FUNCTION random_username()
  RETURNS text
AS $$
    SELECT md5(random()::text || clock_timestamp()::text)::text;
$$ LANGUAGE SQL;


CREATE FUNCTION random_date_of_birth()
  RETURNS date
AS $$
    SELECT (timestamp '1950-01-10 20:00:00' +
       random() * (timestamp '2005-01-20 20:00:00' -
                timestamp '1950-01-10 20:00:00'))::date;
$$ LANGUAGE SQL;


CREATE FUNCTION random_word()
  RETURNS text
AS $$
    select (
        array[
            'requiro', 'plurimum', 'praesum', 'auctoritas', 'pergo', 'abbatis', 'precis',
            'temptatio', 'fusus', 'itis', 'brachants', 'egretudo', 'remuneror', 'coerceo', 'enumero',
            'prenda', 'iterum', 'redeo', 'tantillus', 'corturiacum', 'clementia', 'tergo', 'res', 'pollen', 'saevio', 'lenis', 'eligo', 'unus', 'prout', 'continuus', 'locus', 'fotum', 'prominens', 'nota', 'egre',
            'promutuus', 'ea', 'plector', 'ulciscor', 'prohibeo', 'requievi', 'inflectum', 'rapio', 'quotiens', 'queo', 'eloquens', 'doctum', 'leodie', 'boloniense', 'morsus', 'idem', 'praecedo', 'iaceo', 'rhetoricus', 'munio', 'optimus', 'sapientia', 'scindo', 'devenio',
            'vovi', 'saluto', 'sententia', 'prorsus', 'jugis', 'pervalidus', 'mellis', 'oratio', 'nonus', 'infeste', 'competo', 'sedo', 'expiscor', 'quippe', 'cunctator', 'santiago', 'suffragium', 'culpa', 'incipio', 'quidnam', 'pupugi', 'distringo', 'aliquantus', 'parilis',
            'calco', 'lama', 'glorior', 'lamnia', 'amissus', 'intercipio', 'personam', 'verto', 'decipio', 'civilis', 'dolor', 'universi', 'fabula', 'vulticulus', 'ops', 'emi', 'quantumcumque', 'informatio', 'ager', 'vestri', 'defungo', 'fidelis', 'cursus', 'levamen', 'quicquid',
            'prolicio', 'reprehendo', 'audacter', 'perfeci', 'tremo', 'pevela', 'fugio', 'premo', 'deprehensio', 'oneself', 'pacis', 'peracto', 'cilicium', 'paganus', 'urbs', 'uxor', 'nasci', 'iucundus', 'contemplor', 'ploratus', 'copiae', 'pium', 'rapui', 'iuxta', 'cogo', 'cohibeo', 'estas', 'luxuria'
        ]
    )[floor(random() * 136 + 1)];
$$ LANGUAGE sql;

CREATE FUNCTION random_text()
  RETURNS text
AS $$
    SELECT random_word() || ' ' || random_word() || ' ' || random_word() || ' ' || random_word() || ' ' || random_word();
$$ LANGUAGE SQL;
