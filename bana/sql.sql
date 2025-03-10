-- Trajet 1: Bruxelles à Bruxelles
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Boulevard Anspach', '10', '', '1000', 'Bruxelles', 'Belgium',
    'Avenue Louise', '50', '', '1050', 'Bruxelles', 'Belgium', 3.5, '2025-03-01');

-- Proposed Traject 1
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (13, 5, '09:00:00', '09:30:00', '2025-03-01', 'Bruxelles - Bruxelles', 'Trajet proposé à Bruxelles', 0.5);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (8, 1);

-- Trajet 2: Bruxelles à Bruxelles
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Rue Neuve', '5', '', '1000', 'Bruxelles', 'Belgium',
    'Place Royale', '10', '', '1000', 'Bruxelles', 'Belgium', 2.3, '2025-03-02');

-- Proposed Traject 2
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (14, 5, '10:00:00', '10:30:00', '2025-03-02', 'Bruxelles - Bruxelles', 'Trajet proposé à Bruxelles', 0.3);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (9, 2);

-- Trajet 3: Bruxelles à Bruxelles
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Rue des Sables', '12', '', '1000', 'Bruxelles', 'Belgium',
    'Avenue de la Toison d\Or', '25', '', '1050', 'Bruxelles', 'Belgium', 4.0, '2025-03-03');

-- Proposed Traject 3
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (15, 5, '12:00:00', '12:30:00', '2025-03-03', 'Bruxelles - Bruxelles', 'Trajet proposé à Bruxelles', 0.4);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (10, 3);

-- Trajet 4: Bruxelles à Bruxelles
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Avenue Louise', '30', '', '1050', 'Bruxelles', 'Belgium',
    'Place de Brouckère', '15', '', '1000', 'Bruxelles', 'Belgium', 2.9, '2025-03-04');

-- Proposed Traject 4
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (16, 5, '14:00:00', '14:30:00', '2025-03-04', 'Bruxelles - Bruxelles', 'Trajet proposé à Bruxelles', 0.6);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (11, 1);

-- Trajet 5: Bruxelles à Bruxelles
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Boulevard de Waterloo', '15', '', '1000', 'Bruxelles', 'Belgium',
    'Place Luxembourg', '5', '', '1050', 'Bruxelles', 'Belgium', 3.2, '2025-03-05');

-- Proposed Traject 5
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (17, 5, '16:00:00', '16:30:00', '2025-03-05', 'Bruxelles - Bruxelles', 'Trajet proposé à Bruxelles', 0.7);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (12, 2);

-- Trajet 6: Anvers à Anvers
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Meir', '30', '', '2000', 'Anvers', 'Belgium',
    'Kammenstraat', '20', '', '2000', 'Anvers', 'Belgium', 3.0, '2025-03-06');

-- Proposed Traject 6
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (18, 5, '09:00:00', '09:30:00', '2025-03-06', 'Anvers - Anvers', 'Trajet proposé à Anvers', 0.2);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (13, 1);

-- Trajet 7: Anvers à Anvers
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Keyserlei', '10', '', '2018', 'Anvers', 'Belgium',
    'Meir', '5', '', '2000', 'Anvers', 'Belgium', 1.5, '2025-03-07');

-- Proposed Traject 7
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (19, 5, '10:00:00', '10:30:00', '2025-03-07', 'Anvers - Anvers', 'Trajet proposé à Anvers', 0.3);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (14, 2);

-- Trajet 8: Anvers à Anvers
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Grote Markt', '1', '', '2000', 'Anvers', 'Belgium',
    'Korte Gasthuisstraat', '12', '', '2000', 'Anvers', 'Belgium', 2.8, '2025-03-08');

-- Proposed Traject 8
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (20, 5, '11:00:00', '11:30:00', '2025-03-08', 'Anvers - Anvers', 'Trajet proposé à Anvers', 0.4);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (15, 3);

-- Trajet 9: Anvers à Anvers
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Korte Gasthuisstraat', '7', '', '2000', 'Anvers', 'Belgium',
    'De Keyserlei', '20', '', '2018', 'Anvers', 'Belgium', 1.2, '2025-03-09');

-- Proposed Traject 9
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (21, 5, '12:00:00', '12:30:00', '2025-03-09', 'Anvers - Anvers', 'Trajet proposé à Anvers', 0.2);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (16, 1);

-- Trajet 10: Anvers à Anvers
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Meir', '25', '', '2000', 'Anvers', 'Belgium',
    'Wapper', '14', '', '2000', 'Anvers', 'Belgium', 3.1, '2025-03-10');

-- Proposed Traject 10
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (22, 5, '14:00:00', '14:30:00', '2025-03-10', 'Anvers - Anvers', 'Trajet proposé à Anvers', 0.5);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (17, 2);
-- Trajet 11: Liège à Liège
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Place Saint-Lambert', '1', '', '4000', 'Liège', 'Belgium',
    'Rue Pont d\Avroy', '25', '', '4000', 'Liège', 'Belgium', 2.0, '2025-03-11');

-- Proposed Traject 11
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (23, 5, '09:30:00', '10:00:00', '2025-03-11', 'Liège - Liège', 'Trajet proposé à Liège', 0.3);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (18, 3);

-- Trajet 12: Liège à Liège
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Boulevard de la Sauvenière', '3', '', '4000', 'Liège', 'Belgium',
    'Rue des Guillemins', '40', '', '4000', 'Liège', 'Belgium', 4.1, '2025-03-12');

-- Proposed Traject 12
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (24, 5, '10:30:00', '11:00:00', '2025-03-12', 'Liège - Liège', 'Trajet proposé à Liège', 0.4);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (19, 1);

-- Trajet 13: Liège à Liège
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Place de la République Française', '5', '', '4000', 'Liège', 'Belgium',
    'Avenue de la Liberté', '10', '', '4000', 'Liège', 'Belgium', 3.3, '2025-03-13');

-- Proposed Traject 13
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (25, 5, '11:30:00', '12:00:00', '2025-03-13', 'Liège - Liège', 'Trajet proposé à Liège', 0.2);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (20, 2);

-- Trajet 14: Liège à Liège
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Rue de la Station', '25', '', '4000', 'Liège', 'Belgium',
    'Place du XX Août', '1', '', '4000', 'Liège', 'Belgium', 2.5, '2025-03-14');

-- Proposed Traject 14
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (26, 5, '13:30:00', '14:00:00', '2025-03-14', 'Liège - Liège', 'Trajet proposé à Liège', 0.3);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (21, 3);

-- Trajet 15: Liège à Liège
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Avenue de la Toison d\Or', '10', '', '4000', 'Liège', 'Belgium',
    'Rue du Parc', '5', '', '4000', 'Liège', 'Belgium', 3.0, '2025-03-15');

-- Proposed Traject 15
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (27, 5, '15:00:00', '15:30:00', '2025-03-15', 'Liège - Liège', 'Trajet proposé à Liège', 0.5);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (22, 1);
-- Trajet 16: Gand à Gand
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Korenmarkt', '12', '', '9000', 'Gent', 'Belgium',
    'Veldstraat', '35', '', '9000', 'Gent', 'Belgium', 1.6, '2025-03-16');

-- Proposed Traject 16
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (28, 5, '09:00:00', '09:30:00', '2025-03-16', 'Gent - Gent', 'Trajet proposé à Gand', 0.2);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (23, 1);

-- Trajet 17: Gand à Gand
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Veldstraat', '10', '', '9000', 'Gent', 'Belgium',
    'Korenmarkt', '1', '', '9000', 'Gent', 'Belgium', 2.0, '2025-03-17');

-- Proposed Traject 17
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (29, 5, '10:00:00', '10:30:00', '2025-03-17', 'Gent - Gent', 'Trajet proposé à Gand', 0.3);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (24, 2);

-- Trajet 18: Gand à Gand
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Vrijdagmarkt', '5', '', '9000', 'Gent', 'Belgium',
    'Koningin Elisabethlaan', '12', '', '9000', 'Gent', 'Belgium', 3.1, '2025-03-18');

-- Proposed Traject 18
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (30, 5, '11:00:00', '11:30:00', '2025-03-18', 'Gent - Gent', 'Trajet proposé à Gand', 0.4);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (25, 3);

-- Trajet 19: Gand à Gand
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Kouter', '18', '', '9000', 'Gent', 'Belgium',
    'Oude Beestenmarkt', '14', '', '9000', 'Gent', 'Belgium', 2.3, '2025-03-19');

-- Proposed Traject 19
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (31, 5, '12:30:00', '13:00:00', '2025-03-19', 'Gent - Gent', 'Trajet proposé à Gand', 0.2);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (26, 1);

-- Trajet 20: Gand à Gand
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Kouter', '25', '', '9000', 'Gent', 'Belgium',
    'Sint-Baafsplein', '5', '', '9000', 'Gent', 'Belgium', 1.8, '2025-03-20');

-- Proposed Traject 20
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (32, 5, '13:30:00', '14:00:00', '2025-03-20', 'Gent - Gent', 'Trajet proposé à Gand', 0.1);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (27, 2);
-- Trajet 21: Charleroi à Charleroi
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Place du Manège', '1', '', '6000', 'Charleroi', 'Belgium',
    'Avenue Janson', '20', '', '6000', 'Charleroi', 'Belgium', 2.2, '2025-03-21');

-- Proposed Traject 21
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (33, 5, '09:00:00', '09:30:00', '2025-03-21', 'Charleroi - Charleroi', 'Trajet proposé à Charleroi', 0.3);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (28, 1);

-- Trajet 22: Charleroi à Charleroi
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Avenue Paul Pastur', '8', '', '6000', 'Charleroi', 'Belgium',
    'Boulevard de l\Europe', '15', '', '6000', 'Charleroi', 'Belgium', 3.0, '2025-03-22');

-- Proposed Traject 22
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (34, 5, '10:00:00', '10:30:00', '2025-03-22', 'Charleroi - Charleroi', 'Trajet proposé à Charleroi', 0.4);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (29, 2);

-- Trajet 23: Charleroi à Charleroi
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Rue de la Montagne', '5', '', '6000', 'Charleroi', 'Belgium',
    'Boulevard du Triomphe', '20', '', '6000', 'Charleroi', 'Belgium', 2.7, '2025-03-23');

-- Proposed Traject 23
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (35, 5, '11:30:00', '12:00:00', '2025-03-23', 'Charleroi - Charleroi', 'Trajet proposé à Charleroi', 0.3);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (30, 1);

-- Trajet 24: Charleroi à Charleroi
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Avenue F. Roosevelt', '10', '', '6000', 'Charleroi', 'Belgium',
    'Place de la Station', '10', '', '6000', 'Charleroi', 'Belgium', 3.4, '2025-03-24');

-- Proposed Traject 24
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (36, 5, '13:00:00', '13:30:00', '2025-03-24', 'Charleroi - Charleroi', 'Trajet proposé à Charleroi', 0.5);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (31, 3);

-- Trajet 25: Charleroi à Charleroi
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Place de la Ville Basse', '12', '', '6000', 'Charleroi', 'Belgium',
    'Rue de Charleroi', '22', '', '6000', 'Charleroi', 'Belgium', 2.5, '2025-03-25');

-- Proposed Traject 25
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (37, 5, '14:00:00', '14:30:00', '2025-03-25', 'Charleroi - Charleroi', 'Trajet proposé à Charleroi', 0.2);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (32, 2);
-- Trajet 26: Bruges à Bruges
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Markt', '10', '', '8000', 'Brugge', 'Belgium',
    'Burg', '7', '', '8000', 'Brugge', 'Belgium', 1.5, '2025-03-26');

-- Proposed Traject 26
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (38, 5, '09:00:00', '09:30:00', '2025-03-26', 'Bruges - Bruges', 'Trajet proposé à Bruges', 0.2);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (33, 1);

-- Trajet 27: Bruges à Bruges
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Burg', '5', '', '8000', 'Brugge', 'Belgium',
    'Sint-Jansplein', '12', '', '8000', 'Brugge', 'Belgium', 2.0, '2025-03-27');

-- Proposed Traject 27
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (39, 5, '10:00:00', '10:30:00', '2025-03-27', 'Bruges - Bruges', 'Trajet proposé à Bruges', 0.3);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (34, 2);

-- Trajet 28: Bruges à Bruges
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Vismarkt', '8', '', '8000', 'Brugge', 'Belgium',
    'Langestraat', '14', '', '8000', 'Brugge', 'Belgium', 2.3, '2025-03-28');

-- Proposed Traject 28
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (40, 5, '11:00:00', '11:30:00', '2025-03-28', 'Bruges - Bruges', 'Trajet proposé à Bruges', 0.4);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (35, 1);

-- Trajet 29: Bruges à Bruges
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Ezelstraat', '9', '', '8000', 'Brugge', 'Belgium',
    'Rozenhoedkaai', '5', '', '8000', 'Brugge', 'Belgium', 1.7, '2025-03-29');

-- Proposed Traject 29
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (41, 5, '12:00:00', '12:30:00', '2025-03-29', 'Bruges - Bruges', 'Trajet proposé à Bruges', 0.2);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (36, 3);

-- Trajet 30: Bruges à Bruges
INSERT INTO trajects_traject
    (start_street, start_number, start_box, start_zp, start_locality, start_country,
    end_street, end_number, end_box, end_zp, end_locality, end_country, distance, date)
VALUES
    ('Nieuwe Gentweg', '11', '', '8000', 'Brugge', 'Belgium',
    'Katelijnestraat', '15', '', '8000', 'Brugge', 'Belgium', 2.5, '2025-03-30');

-- Proposed Traject 30
INSERT INTO trajects_proposedtraject
    (traject_id, member_id, departure_time, arrival_time, date, name, details, detour_distance)
VALUES
    (42, 5, '13:00:00', '13:30:00', '2025-03-30', 'Bruges - Bruges', 'Trajet proposé à Bruges', 0.3);

-- Liaison transport modes
INSERT INTO trajects_proposedtraject_transport_modes
    (proposedtraject_id, transportmode_id)
VALUES
    (37, 2);
