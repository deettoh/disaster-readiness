-- Seed data for Petaling Jaya Disaster Readiness
-- This file is loaded by `supabase db reset` after migrations.
-- It contains static reference data that does not require Python libraries.

-- Shelters: Petaling Jaya Community Centers (Evacuation Points)
-- Source: OpenStreetMap community_centre/townhall/civic tags, filtered for PJ.
-- Coordinates from OSM via osmnx (WGS84 / EPSG:4326).

TRUNCATE TABLE public.shelters RESTART IDENTITY CASCADE;

INSERT INTO public.shelters (name, capacity, geom, address)
VALUES
    (
        'Dewan Serbaguna Sungai Way',
        0,
        extensions.ST_SetSRID(extensions.ST_MakePoint(101.620848, 3.0866757)::extensions.geography, 4326),
        'Sungai Way, Petaling Jaya'
    ),
    (
        'Dewan Atria Damansara Jaya',
        0,
        extensions.ST_SetSRID(extensions.ST_MakePoint(101.6169977, 3.1269922)::extensions.geography, 4326),
        'Damansara Jaya, Petaling Jaya'
    ),
    (
        'D''Buana Hall',
        0,
        extensions.ST_SetSRID(extensions.ST_MakePoint(101.6371259, 3.0787015)::extensions.geography, 4326),
        'Petaling Jaya'
    ),
    (
        'Dewan Komuniti PJS 6',
        0,
        extensions.ST_SetSRID(extensions.ST_MakePoint(101.61533854070717, 3.080794791008773)::extensions.geography, 4326),
        'PJS 6, Petaling Jaya'
    ),
    (
        'Dewan Komuniti (Unspecified)',
        0,
        extensions.ST_SetSRID(extensions.ST_MakePoint(101.63215211256305, 3.1190012909967546)::extensions.geography, 4326),
        'Petaling Jaya'
    );
