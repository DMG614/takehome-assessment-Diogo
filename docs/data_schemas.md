# Data Schemas

## EPA Vehicles (Cleaned)

| Column | Description |
|--------|-------------|
| `year` | Model year |
| `make` | Vehicle manufacturer |
| `model` | Vehicle model name |
| `VClass` | Vehicle class (sedan, SUV, truck, etc.) |
| `drive` | Drive type (FWD, RWD, AWD, 4WD) |
| `trany` | Transmission type |
| `cylinders` | Number of engine cylinders |
| `displ` | Engine displacement in liters (engine size) |
| `fuelType` | Primary fuel type (Gasoline, Diesel, Electric, etc.) |
| `fuelType1` | Secondary fuel type (for dual-fuel vehicles) |
| `city08` | City MPG - fuel efficiency in stop-and-go traffic (08 = 2008 EPA test standard) |
| `highway08` | Highway MPG - fuel efficiency at steady highway speed |
| `comb08` | Combined MPG - weighted average|
| `co2TailpipeGpm` | CO2 emissions in grams per mile |
| `id` | Unique vehicle ID |

**Note on "08" suffix:** These columns use the 2008 EPA testing methodology, which is more realistic than pre-2008 standards. For electric vehicles, MPG is actually MPGe (miles per gallon equivalent).

## NHTSA Complaints (Raw)

| Column | Description |
|--------|-------------|
| `ODINO` | Unique complaint ID |
| `DATEA` | Date complaint received |
| `YEARTXT` | Vehicle year |
| `MAKETXT` | Vehicle make |
| `MODELTXT` | Vehicle model |
| `MFGTXT` | Manufacturer name |
| `CMPLID` | Complaint description/summary |
| `COMPDESC` | Failed component description |
| `CRASH` | Crash occurred (Y/N) |
| `FIRE` | Fire occurred (Y/N) |
| `INJURED` | Number of injuries |
| `DEATHS` | Number of deaths |
| `MILEAGE` | Odometer reading at complaint |
| `VIN` | Vehicle Identification Number |

## DOE Fuel Stations (Raw)

| Column | Description |
|--------|-------------|
| `fuel_type_code` | Fuel type code: ELEC (electric), LNG (liquefied natural gas), CNG (compressed natural gas), BD (biodiesel), E85 (85% ethanol), HY (hydrogen) |
| `station_name` | Station name |
| `street_address` | Street address |
| `city` | City |
| `state` | State abbreviation |
| `zip` | ZIP code |
| `latitude` | Latitude coordinate (for mapping) |
| `longitude` | Longitude coordinate (for mapping) |
| `status_code` | Status: E (available), P (planned), T (temporarily unavailable) |
| `access_code` | Access type (public or private) |
| `open_date` | Date station opened |
| `ev_network` | EV charging network (ChargePoint, Tesla Supercharger, Electrify America, etc.) |
| `ev_connector_types` | Types of charging connectors available (CHAdeMO, CCS, J1772, Tesla) |
| `ev_pricing` | Pricing information for charging |
