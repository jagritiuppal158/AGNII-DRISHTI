# Agni-Drishti API Contract

> **Version**: 1.0.0
> **Base URL**: `https://api.agni-drishti.example.com/v1`
> **Format**: All requests and responses use `application/json`.

---

## Authentication

All endpoints require a valid Bearer token. For the demo environment, a single shared token is used.

**Obtaining a token** is outside the scope of this document; the token is distributed as part of the demo credentials.

Include the token in every request:

```
Authorization: Bearer <token>
```

Unauthorized requests return:

```json
HTTP 401 Unauthorized
{
  "error": "unauthorized",
  "message": "Missing or invalid token."
}
```

---

## Classification Classes

The five valid classification strings used throughout this API are:

| Class | Description |
|---|---|
| `industrial_fire` | Fire originating from an industrial facility |
| `wildfire` | Uncontrolled fire in a natural/forest area |
| `crop_burning` | Agricultural stubble or crop residue burning |
| `gas_flare` | Continuous flaring from oil/gas extraction |
| `mining` | Thermal anomaly from mining operations |

---

## Common Field Types

| Field | Type | Notes |
|---|---|---|
| `id` | `string` (UUID v4) | All IDs are UUIDs |
| `timestamp` | `string` (ISO 8601) | e.g. `"2025-09-06T06:30:00Z"` |
| `latitude` | `number` | Decimal degrees, WGS-84 |
| `longitude` | `number` | Decimal degrees, WGS-84 |
| `confidence` | `number` | Float in `[0.0, 1.0]` |
| `risk_level` | `string` | One of `"low"`, `"medium"`, `"high"`, `"critical"` |
| `classification` | `string` | One of the five class strings above |

---

## Endpoints

---

### 1. List Hotspots

Retrieve a paginated list of thermal hotspot detections, with optional filters.

**`GET /hotspots`**

#### Auth Required
Yes

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `region` | `string` | No | Region/state name or ISO 3166-2 code to filter by |
| `class` | `string` | No | Filter by classification class (one of the five strings) |
| `risk` | `string` | No | Filter by risk level: `low`, `medium`, `high`, `critical` |
| `date_from` | `string` (ISO 8601 date) | No | Earliest detection date, inclusive (e.g. `2025-08-01`) |
| `date_to` | `string` (ISO 8601 date) | No | Latest detection date, inclusive |
| `page` | `integer` | No | Page number, default `1` |
| `page_size` | `integer` | No | Results per page, default `50`, max `200` |

#### Response `200 OK`

```json
{
  "page": 1,
  "page_size": 50,
  "total": 142,
  "results": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "detected_at": "2025-09-05T14:22:00Z",
      "latitude": 28.6139,
      "longitude": 77.2090,
      "region": "Delhi",
      "classification": "crop_burning",
      "confidence": 0.87,
      "risk_level": "high",
      "location_id": "loc-uuid-or-null",
      "source": "FIRMS_MODIS"
    }
  ]
}
```

#### Error Responses

| Status | `error` | Reason |
|---|---|---|
| `400` | `invalid_filter` | Unknown `class` or `risk` value |
| `401` | `unauthorized` | Missing or invalid token |

---

### 2. Hotspot Detail + Evidence

Retrieve full detail for a single hotspot, including raw satellite evidence fields.

**`GET /hotspots/{id}`**

#### Auth Required
Yes

#### Path Parameters

| Parameter | Type | Description |
|---|---|---|
| `id` | `string` (UUID) | Hotspot ID |

#### Response `200 OK`

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "detected_at": "2025-09-05T14:22:00Z",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "region": "Delhi",
  "classification": "crop_burning",
  "confidence": 0.87,
  "risk_level": "high",
  "location_id": "loc-uuid-or-null",
  "source": "FIRMS_MODIS",
  "evidence": {
    "brightness_temp_kelvin": 342.5,
    "frp_mw": 18.3,
    "scan_deg": 1.1,
    "track_deg": 1.0,
    "satellite": "Terra",
    "instrument": "MODIS",
    "daynight": "D",
    "raw_confidence_pct": 87
  },
  "thumbnail_url": "https://storage.agni-drishti.example.com/tiles/a1b2c3d4.png"
}
```

#### Error Responses

| Status | `error` | Reason |
|---|---|---|
| `401` | `unauthorized` | Missing or invalid token |
| `404` | `not_found` | No hotspot with that ID |

---

### 3. Classify a Hotspot

Submit a hotspot feature vector to the classifier and receive a predicted class with per-class probabilities.

**`POST /classify`**

#### Auth Required
Yes

#### Request Body

```json
{
  "latitude": 28.6139,
  "longitude": 77.2090,
  "brightness_temp_kelvin": 342.5,
  "frp_mw": 18.3,
  "scan_deg": 1.1,
  "track_deg": 1.0,
  "daynight": "D",
  "satellite": "Terra",
  "detected_at": "2025-09-05T14:22:00Z"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `latitude` | `number` | Yes | |
| `longitude` | `number` | Yes | |
| `brightness_temp_kelvin` | `number` | Yes | Brightness temperature in Kelvin |
| `frp_mw` | `number` | Yes | Fire radiative power in MW |
| `scan_deg` | `number` | No | Along-scan pixel size in degrees |
| `track_deg` | `number` | No | Along-track pixel size in degrees |
| `daynight` | `string` | No | `"D"` or `"N"` |
| `satellite` | `string` | No | Satellite name |
| `detected_at` | `string` | No | ISO 8601 timestamp of detection |

#### Response `200 OK`

```json
{
  "classification": "crop_burning",
  "confidence": 0.87,
  "probabilities": {
    "industrial_fire": 0.04,
    "wildfire": 0.06,
    "crop_burning": 0.87,
    "gas_flare": 0.02,
    "mining": 0.01
  },
  "risk_level": "high"
}
```

#### Error Responses

| Status | `error` | Reason |
|---|---|---|
| `400` | `missing_fields` | Required fields absent from body |
| `400` | `invalid_value` | Field out of expected range |
| `401` | `unauthorized` | Missing or invalid token |
| `422` | `unprocessable` | Features could not be processed by model |

---

### 4. Hotspot Recurrence Timeline for a Location

Retrieve a chronological list of all hotspot detections ever linked to a persistent thermal-source location.

**`GET /history/{location_id}`**

#### Auth Required
Yes

#### Path Parameters

| Parameter | Type | Description |
|---|---|---|
| `location_id` | `string` (UUID) | The persistent location ID |

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `date_from` | `string` (ISO 8601 date) | No | Filter from this date, inclusive |
| `date_to` | `string` (ISO 8601 date) | No | Filter to this date, inclusive |
| `page` | `integer` | No | Default `1` |
| `page_size` | `integer` | No | Default `50`, max `200` |

#### Response `200 OK`

```json
{
  "location_id": "loc-uuid-here",
  "location_name": "Sector 12 Industrial Cluster, Gurugram",
  "page": 1,
  "page_size": 50,
  "total": 23,
  "timeline": [
    {
      "id": "hotspot-uuid",
      "detected_at": "2025-09-05T14:22:00Z",
      "classification": "industrial_fire",
      "confidence": 0.91,
      "risk_level": "critical",
      "frp_mw": 45.2,
      "source": "FIRMS_VIIRS"
    },
    {
      "id": "hotspot-uuid-2",
      "detected_at": "2025-08-22T09:10:00Z",
      "classification": "industrial_fire",
      "confidence": 0.88,
      "risk_level": "high",
      "frp_mw": 38.7,
      "source": "FIRMS_MODIS"
    }
  ]
}
```

#### Error Responses

| Status | `error` | Reason |
|---|---|---|
| `401` | `unauthorized` | Missing or invalid token |
| `404` | `not_found` | No location with that ID |

---

### 5. Submit Feedback on a Hotspot Classification

An analyst confirms, rejects, or marks a classification as uncertain.

**`POST /feedback`**

#### Auth Required
Yes

#### Request Body

```json
{
  "hotspot_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "verdict": "confirm",
  "corrected_class": null,
  "notes": "Visually confirmed via Sentinel-2 imagery."
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `hotspot_id` | `string` (UUID) | Yes | The hotspot being reviewed |
| `verdict` | `string` | Yes | One of `"confirm"`, `"reject"`, `"uncertain"` |
| `corrected_class` | `string` or `null` | Conditional | Required (can be `null`) when `verdict` is `"reject"`. Must be one of the five class strings, or `null` if correct class is unknown |
| `notes` | `string` or `null` | No | Free-text analyst note, max 1000 characters |

#### Response `201 Created`

```json
{
  "id": "feedback-uuid",
  "hotspot_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "verdict": "confirm",
  "corrected_class": null,
  "notes": "Visually confirmed via Sentinel-2 imagery.",
  "submitted_at": "2025-09-06T06:45:00Z"
}
```

#### Error Responses

| Status | `error` | Reason |
|---|---|---|
| `400` | `missing_fields` | `hotspot_id` or `verdict` absent |
| `400` | `invalid_verdict` | `verdict` not one of the three allowed values |
| `400` | `invalid_class` | `corrected_class` not one of the five class strings |
| `400` | `corrected_class_required` | `verdict` is `"reject"` but `corrected_class` key is missing entirely |
| `401` | `unauthorized` | Missing or invalid token |
| `404` | `not_found` | No hotspot with that ID |

---

### 6. Feedback Counts

Retrieve aggregate feedback counts across all hotspots, useful for dashboard summaries.

**`GET /feedback/count`**

#### Auth Required
Yes

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `hotspot_id` | `string` (UUID) | No | Scope counts to a single hotspot |
| `classification` | `string` | No | Scope to hotspots of a given class |

#### Response `200 OK`

```json
{
  "total": 381,
  "confirm": 290,
  "reject": 68,
  "uncertain": 23,
  "by_class": {
    "industrial_fire": { "confirm": 80, "reject": 10, "uncertain": 5 },
    "wildfire":        { "confirm": 75, "reject": 20, "uncertain": 8 },
    "crop_burning":    { "confirm": 90, "reject": 15, "uncertain": 5 },
    "gas_flare":       { "confirm": 30, "reject": 13, "uncertain": 3 },
    "mining":          { "confirm": 15, "reject": 10, "uncertain": 2 }
  }
}
```

#### Error Responses

| Status | `error` | Reason |
|---|---|---|
| `401` | `unauthorized` | Missing or invalid token |

---

### 7. List Persistent Thermal-Source Locations

List all persistent thermal-source locations with their current classification, confidence, and monitoring status.

**`GET /locations`**

#### Auth Required
Yes

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `region` | `string` | No | Filter by region name or code |
| `class` | `string` | No | Filter by dominant classification class |
| `status` | `string` | No | Filter by status: `active`, `monitoring`, `resolved` |
| `page` | `integer` | No | Default `1` |
| `page_size` | `integer` | No | Default `50`, max `200` |

#### Response `200 OK`

```json
{
  "page": 1,
  "page_size": 50,
  "total": 18,
  "results": [
    {
      "id": "loc-uuid-here",
      "name": "Sector 12 Industrial Cluster, Gurugram",
      "latitude": 28.4595,
      "longitude": 77.0266,
      "region": "Haryana",
      "current_classification": "industrial_fire",
      "current_confidence": 0.91,
      "status": "active",
      "first_detected_at": "2024-11-03T07:00:00Z",
      "last_detected_at": "2025-09-05T14:22:00Z",
      "hotspot_count": 23,
      "open_case_id": "case-uuid-or-null"
    }
  ]
}
```

#### Error Responses

| Status | `error` | Reason |
|---|---|---|
| `400` | `invalid_filter` | Unknown `class` or `status` value |
| `401` | `unauthorized` | Missing or invalid token |

---

### 8. Location Detail

Full detail for a single persistent thermal-source location, including linked hotspot history and any associated enforcement case.

**`GET /locations/{id}`**

#### Auth Required
Yes

#### Path Parameters

| Parameter | Type | Description |
|---|---|---|
| `id` | `string` (UUID) | Location ID |

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `page` | `integer` | No | Page for `hotspot_history`, default `1` |
| `page_size` | `integer` | No | Default `50`, max `200` |

#### Response `200 OK`

```json
{
  "id": "loc-uuid-here",
  "name": "Sector 12 Industrial Cluster, Gurugram",
  "latitude": 28.4595,
  "longitude": 77.0266,
  "region": "Haryana",
  "current_classification": "industrial_fire",
  "current_confidence": 0.91,
  "status": "active",
  "first_detected_at": "2024-11-03T07:00:00Z",
  "last_detected_at": "2025-09-05T14:22:00Z",
  "hotspot_count": 23,
  "case": {
    "id": "case-uuid",
    "status": "investigating",
    "opened_at": "2025-08-01T10:00:00Z",
    "last_updated_at": "2025-09-04T09:00:00Z"
  },
  "hotspot_history": {
    "page": 1,
    "page_size": 50,
    "total": 23,
    "results": [
      {
        "id": "hotspot-uuid",
        "detected_at": "2025-09-05T14:22:00Z",
        "classification": "industrial_fire",
        "confidence": 0.91,
        "risk_level": "critical",
        "frp_mw": 45.2,
        "source": "FIRMS_VIIRS"
      }
    ]
  }
}
```

> **Note**: `case` is `null` if no case has been opened for this location.

#### Error Responses

| Status | `error` | Reason |
|---|---|---|
| `401` | `unauthorized` | Missing or invalid token |
| `404` | `not_found` | No location with that ID |

---

### 9. Open a Case on a Location

Create a new enforcement case linked to a persistent thermal-source location. Status is always initialized to `"open"`.

**`POST /cases`**

#### Auth Required
Yes

#### Request Body

```json
{
  "location_id": "loc-uuid-here",
  "title": "Repeated industrial burning - Sector 12",
  "notes": "Third recurrence in 90 days. Escalation warranted."
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `location_id` | `string` (UUID) | Yes | The persistent location to link the case to |
| `title` | `string` | Yes | Short descriptive title, max 200 characters |
| `notes` | `string` or `null` | No | Initial case notes, max 2000 characters |

#### Response `201 Created`

```json
{
  "id": "case-uuid",
  "location_id": "loc-uuid-here",
  "title": "Repeated industrial burning - Sector 12",
  "status": "open",
  "notes": "Third recurrence in 90 days. Escalation warranted.",
  "opened_at": "2025-09-06T07:00:00Z",
  "last_updated_at": "2025-09-06T07:00:00Z"
}
```

#### Error Responses

| Status | `error` | Reason |
|---|---|---|
| `400` | `missing_fields` | `location_id` or `title` absent |
| `400` | `case_already_open` | An open case already exists for this location |
| `401` | `unauthorized` | Missing or invalid token |
| `404` | `not_found` | No location with that `location_id` |

---

### 10. Update a Case

Update the status or add notes to an existing case. Only provided fields are updated (partial update semantics).

**`PATCH /cases/{id}`**

#### Auth Required
Yes

#### Path Parameters

| Parameter | Type | Description |
|---|---|---|
| `id` | `string` (UUID) | Case ID |

#### Request Body

All fields are optional; include only those to be changed.

```json
{
  "status": "investigating",
  "notes": "Field inspection scheduled for 2025-09-10."
}
```

| Field | Type | Allowed Values |
|---|---|---|
| `status` | `string` | `"open"`, `"investigating"`, `"notice_issued"`, `"escalated"`, `"closed"` |
| `notes` | `string` or `null` | Appended to case audit history. Max 2000 characters |

#### Case Status Lifecycle

```
open -> investigating -> notice_issued -> escalated -> closed
         ^______________^                              ^
                                    (any state can transition to closed)
```

#### Response `200 OK`

```json
{
  "id": "case-uuid",
  "location_id": "loc-uuid-here",
  "title": "Repeated industrial burning - Sector 12",
  "status": "investigating",
  "history": [
    {
      "changed_at": "2025-09-06T07:00:00Z",
      "status": "open",
      "notes": "Third recurrence in 90 days. Escalation warranted."
    },
    {
      "changed_at": "2025-09-06T09:15:00Z",
      "status": "investigating",
      "notes": "Field inspection scheduled for 2025-09-10."
    }
  ],
  "opened_at": "2025-09-06T07:00:00Z",
  "last_updated_at": "2025-09-06T09:15:00Z"
}
```

#### Error Responses

| Status | `error` | Reason |
|---|---|---|
| `400` | `invalid_status` | `status` not one of the five allowed values |
| `400` | `invalid_transition` | Attempted status change is not a valid transition |
| `401` | `unauthorized` | Missing or invalid token |
| `404` | `not_found` | No case with that ID |

---

### 11. List Cases

Retrieve a paginated list of enforcement cases, filterable by status.

**`GET /cases`**

#### Auth Required
Yes

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `status` | `string` | No | Filter by: `open`, `investigating`, `notice_issued`, `escalated`, `closed` |
| `location_id` | `string` (UUID) | No | Filter cases linked to a specific location |
| `date_from` | `string` (ISO 8601 date) | No | Filter by `opened_at` date, inclusive |
| `date_to` | `string` (ISO 8601 date) | No | Filter by `opened_at` date, inclusive |
| `page` | `integer` | No | Default `1` |
| `page_size` | `integer` | No | Default `50`, max `200` |

#### Response `200 OK`

```json
{
  "page": 1,
  "page_size": 50,
  "total": 7,
  "results": [
    {
      "id": "case-uuid",
      "location_id": "loc-uuid-here",
      "location_name": "Sector 12 Industrial Cluster, Gurugram",
      "title": "Repeated industrial burning - Sector 12",
      "status": "investigating",
      "opened_at": "2025-09-06T07:00:00Z",
      "last_updated_at": "2025-09-06T09:15:00Z"
    }
  ]
}
```

#### Error Responses

| Status | `error` | Reason |
|---|---|---|
| `400` | `invalid_filter` | Unknown `status` value |
| `401` | `unauthorized` | Missing or invalid token |

---

## Error Response Shape

All errors follow a consistent envelope:

```json
{
  "error": "error_code_snake_case",
  "message": "Human-readable description of the error.",
  "details": {}
}
```

`details` is optional and may contain field-level validation messages.

---

## Pagination

All list endpoints share the same pagination query parameters and response envelope fields:

| Query param | Default | Max |
|---|---|---|
| `page` | `1` | - |
| `page_size` | `50` | `200` |

Response envelope always includes `page`, `page_size`, and `total` (total matching records across all pages).

---

## Endpoint Summary

| # | Method | Path | Description |
|---|---|---|---|
| 1 | `GET` | `/hotspots` | List hotspots with filters |
| 2 | `GET` | `/hotspots/{id}` | Single hotspot + evidence |
| 3 | `POST` | `/classify` | Classify a feature vector |
| 4 | `GET` | `/history/{location_id}` | Recurrence timeline for a location |
| 5 | `POST` | `/feedback` | Submit confirm/reject/uncertain verdict |
| 6 | `GET` | `/feedback/count` | Aggregate feedback counts |
| 7 | `GET` | `/locations` | List persistent thermal-source locations |
| 8 | `GET` | `/locations/{id}` | Location detail + history + case |
| 9 | `POST` | `/cases` | Open a case on a location |
| 10 | `PATCH` | `/cases/{id}` | Update case status / add notes |
| 11 | `GET` | `/cases` | List cases, filterable by status |
