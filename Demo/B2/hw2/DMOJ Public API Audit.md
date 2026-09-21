# DMOJ Public API Audit
From overlook, it looks like RESTful

But the Cachability doesn't specify in the docs, so it kinda created a gray area here.

So, RESTful-ish, but not RESTful.

## Query Parameters for APIs

Most of the API endpoints support **filtering via query parameters**. There are **two types of filtering** that are supported, *basic filtering and list filtering*. Basic filtering allows filtering for a single value, while list filtering allows filtering for a group of values. Each endpoint describes the filtering that it supports, with the name in a codeblock being the query parameter name.

Example of basic filtering: `/api/v2/problems?partial=True` - This will only return problems with partial points enabled.

Example of list filtering: `/api/v2/problems?organization=1&organization=2&type=Implementation` - This will only return problems (private to organizations 1 OR 2) AND (problem type is Implementation)

## Format

**All responses** are of the following structure:
```json
{
    "api_version": "2.0",
    "method": "<HTTP method that was used>",
    "fetched": "<time that the request was made in ISO format>",
    "data": "<rest of the data>",
    "error": "<any errors that were encountered>"
}
```

It is guaranteed that only **one of data or error will be in the response**.

### Error format
```json
{
    "error": {
        "code": "<HTTP status code>",
        "message": "<error message>"
    }
}
```

### Data format
The data format differs depending on the endpoint called. For endpoints that respond with a single object:
```json
{
    "data": {
        "object": "<object data>"
    }
}
```

For endpoints that respond with a list of objects:

```json
{
    "data": {
        "current_object_count": "<number of objects in the current page>",
        "objects_per_page": "<maximum number of objects that will ever appear on a single page>",
        "total_objects": "<total number of objects in the list>",
        "page_index": "<the current page's index, one indexed>",
        "total_pages": "<total number of pages>",
        "objects": [
            "<list of object data>"
        ]
    }
}
```

## Endpoints

### [`/api/v2/contests`]()

Example: [/api/v2/contests?tag=seasonal&tag=dmopc](https://dmoj.ca/api/v2/contests?tag=seasonal&tag=dmopc)

#### [Basic filters](#/site/api?id=basic-filters)

*   `is_rated` - boolean

#### [List filters](#/site/api?id=list-filters)

*   `key` - contest key
*   `tag` - tag name
*   `organization` - organization id

#### [Object response](#/site/api?id=object-response)

    {
        "key": "<contest key>",
        "name": "<contest name>",
        "start_time": "<contest start time in ISO format>",
        "end_time": "<contest end time in ISO format>",
        "is_rated": "<whether the contest is rated>",
        "rate_all": "<whether the contest is rated on join>",
        "time_limit": "<contest time limit in seconds, or null if the contest is not windowed>",
        "tags": [
            "<list of tag name>"
        ]
    }

### [`/api/v2/contest/<contest key>`](#/site/api?id=apiv2contestltcontest-keygt)

Example: [/api/v2/contest/bts19](https://dmoj.ca/api/v2/contest/bts19)

#### [Object response](#/site/api?id=object-response-1)

    {
        "key": "<contest key>",
        "name": "<contest name>",
        "start_time": "<contest start time in ISO format>",
        "end_time": "<contest end time in ISO format>",
        "time_limit": "<contest time limit in seconds, or null if the contest is not windowed>",
        "is_rated": "<whether the contest is rated>",
        "rate_all": "<whether the contest is rated on join>",
        "has_rating": "<whether the contest has been rated>",
        "rating_floor": "<the minimum user rating required for the user to be rated, or null if there is no minimum>",
        "rating_ceiling": "<the maximum user rating for the user to be rated, or null if there is no maximum>",
        "performance_ceiling": "<the maximum user rating possible from this contest, or null if there is no maximum>",
        "hidden_scoreboard": "<whether the contest's scoreboard is hidden>",
        "scoreboard_visibility": "<whether the scoreboard is (V)isible, visible after (C)ontest, or visible after (P)articipation>",
        "is_organization_private": "<whether the contest is private to organizations>",
        "organizations": [
            "<list of organization id>"
        ],
        "is_private": "<whether the contest is private to specific users>",
        "tags": [
            "<list of tag name>"
        ],
        "format": {
            "name": "<the name of the contest format>",
            "config": "<the contest format JSON configuration>"
        },
        "problems": [
            {
                "points": "<the integer amount of points the problem is worth in contest>",
                "partial": "<whether it is possible to achieve partial points on the problem>",
                "is_pretested": "<whether the problem is pretested>",
                "max_submissions": "<the maximum number of submissions allowed, or null if there is no limit>",
                "label": "<the label for this problem>",
                "name": "<problem name>",
                "code": "<problem code>"
            }
        ],
        "rankings": [
            {
                "user": "<participant username>",
                "start_time": "<effective participation start time in ISO format>",
                "end_time": "<participation end time in ISO format>",
                "score": "<participant score>",
                "cumulative_time": "<participant cumulative time, dependent on the contest format>",
                "tiebreaker": "<participant tiebreaker value>",
                "old_rating": "<participant rating before the contest, or null if not rated>",
                "new_rating": "<participant rating after the contest, or null if not rated>",
                "is_disqualified": "<whether this participant is disqualified>",
                "solutions": [
                    "<list of contest format-dependent dictionaries for individual problem scores>"
                ]
            }
        ]
    }

### [`/api/v2/participations`](#/site/api?id=apiv2participations)

Example: [/api/v2/participations?contest=dmopc19c6&virtual\_participation\_number=0&is\_disqualified=True](https://dmoj.ca/api/v2/participations?contest=dmopc19c6&virtual_participation_number=0&is_disqualified=True)

#### [Basic filters](#/site/api?id=basic-filters-1)

*   `contest` - contest key
*   `user` - user username
*   `is_disqualified` - boolean
*   `virtual_participation_number` - non-negative integer

#### [Object response](#/site/api?id=object-response-2)

    {
        "user": "<participant username>",
        "contest": "<contest key>",
        "start_time": "<effective participation start time in ISO format>",
        "end_time": "<participation end time in ISO format>",
        "score": "<participant score>",
        "cumulative_time": "<participant cumulative time, dependent on the contest format>",
        "tiebreaker": "<participant tiebreaker value>",
        "is_disqualified": "<whether this participant is disqualified>",
        "virtual_participation_number": "<virtual participation number>"
    }

### [`/api/v2/problems`](#/site/api?id=apiv2problems)

Example: [/api/v2/problems?partial=True&type=Uncategorized](https://dmoj.ca/api/v2/problems?partial=True&type=Uncategorized)

#### [Basic filters](#/site/api?id=basic-filters-2)

*   `partial` - boolean

#### [List filters](#/site/api?id=list-filters-1)

*   `code` - problem code
*   `group` - problem group full name
*   `type` - problem type full name
*   `organization` - organization id

#### [Additional filters](#/site/api?id=additional-filters)

*   `search` - similar to a list filter, except searches for the list of parameters in the problem's name, code, and description.

#### [Object response](#/site/api?id=object-response-3)

    {
        "code": "<problem code>",
        "name": "<problem name>",
        "types": [
            "<list of type full name>"
        ],
        "group": "<problem group full name>",
        "points": "<problem points>",
        "partial": "<whether partials are enabled for this problem>",
        "is_organization_private": "<whether the problem is private to organizations>",
        "is_public": "<whether the problem is publicly visible>"
    }

### [`/api/v2/problem/<problem code>`](#/site/api?id=apiv2problemltproblem-codegt)

Example: [/api/v2/problem/helloworld](https://dmoj.ca/api/v2/problem/helloworld)

#### [Object response](#/site/api?id=object-response-4)

    {
        "code": "<problem code>",
        "name": "<problem name>",
        "authors": [
            "<list of author username>"
        ],
        "types": [
            "<list of type full name>"
        ],
        "group": "<problem group full name>",
        "time_limit": "<problem time limit>",
        "memory_limit": "<problem memory limit>",
        "language_resource_limits": [
            {
                "language": "<language key>",
                "time_limit": "<language-specific time limit>",
                "memory_limit": "<language-specific memory limit>"
            }
        ],
        "points": "<problem points>",
        "partial": "<whether partials are enabled for this problem>",
        "short_circuit": "<whether short circuit is enabled for this problem>",
        "languages": [
            "<list of language key>"
        ],
        "is_organization_private": "<whether the problem is private to organizations>",
        "organizations": [
            "<list of organization id>"
        ],
        "is_public": "<whether the problem is publicly visible>"
    }

#### [Additional info](#/site/api?id=additional-info)

`is_public`: Whether the problem is publicly visible to the organizations listed. If `is_organization_private` is `false`, the problem is visible to all users.

### [`/api/v2/users`](#/site/api?id=apiv2users)

Example: [/api/v2/users?organization=8](https://dmoj.ca/api/v2/users?organization=8)

#### [List filters](#/site/api?id=list-filters-2)

*   `id` - user id
*   `username` - user username
*   `organization` - organization id

#### [Object response](#/site/api?id=object-response-5)

    {
        "id": "<user id>",
        "username": "<user username>",
        "points": "<user points>",
        "performance_points": "<user performance points>",
        "problem_count": "<number of problems the user has solved>",
        "rank": "<user display rank>",
        "rating": "<user rating>"
    }

### [`/api/v2/user/<user username>`](#/site/api?id=apiv2userltuser-usernamegt)

Example: [/api/v2/user/Xyene](https://dmoj.ca/api/v2/user/Xyene)

#### [Object response](#/site/api?id=object-response-6)

    {
        "id": "<user id>",
        "username": "<user username>",
        "points": "<user points>",
        "performance_points": "<user performance points>",
        "problem_count": "<number of problems the user has solved>",
        "solved_problems": [
            "<list of problem code>"
        ],
        "rank": "<user display rank>",
        "rating": "<user rating>",
        "organizations": [
            "<list of organization id>"
        ],
        "contests": [
            {
                "key": "<contest key>",
                "score": "<user score>",
                "cumulative_time": "<user cumulative time, dependent on the contest format>",
                "rating": "<user rating after this contest, or null if not rated>",
                "raw_rating": "<user raw rating after this contest, or null if not rated>",
                "performance": "<user performance, or null if not rated>"
            }
        ]
    }

### [`/api/v2/submissions`](#/site/api?id=apiv2submissions)

Example: [/api/v2/submissions?user=Ninjaclasher](https://dmoj.ca/api/v2/submissions?user=Ninjaclasher)

#### [Basic filters](#/site/api?id=basic-filters-3)

*   `user` - user username
*   `problem` - problem code

#### [List filters](#/site/api?id=list-filters-3)

*   `id` - submission id
*   `language` - language key
*   `result` - string

#### [Object response](#/site/api?id=object-response-7)

    {
        "id": "<submission id>",
        "problem": "<problem code>",
        "user": "<user username>",
        "date": "<submission date in ISO format>",
        "language": "<language key>",
        "time": "<submission time usage>",
        "memory": "<submission memory usage>",
        "points": "<submission points awarded>",
        "result": "<submission result>"
    }

### [`/api/v2/submission/<submission id>`](#/site/api?id=apiv2submissionltsubmission-idgt)

Example: [/api/v2/submission/1000000](https://dmoj.ca/api/v2/submission/1000000)

#### [Object response](#/site/api?id=object-response-8)

    {
        "id": "<submission id>",
        "problem": "<problem code>",
        "user": "<user username>",
        "date": "<submission date in ISO format>",
        "time": "<submission time usage>",
        "memory": "<submission memory usage>",
        "points": "<submission points awarded>",
        "language": "<language key>",
        "status": "<submission status>",
        "result": "<submission result>",
        "case_points": "<submission case points>",
        "case_total": "<submission case total>",
        "cases": [
            "<list of case or batch data>"
        ]
    }

#### [Additional info](#/site/api?id=additional-info-1)

`case or batch data`: Each object will be one of the following, depending on whether the current case is a batch or a single test case:

#### [Case data](#/site/api?id=case-data)

    {
        "type": "case",
        "case_id": "<case id>",
        "status": "<case status>",
        "time": "<case time usage>",
        "memory": "<case memory usage>",
        "points": "<case points awarded>",
        "total": "<case total points>"
    }

#### [Batch data](#/site/api?id=batch-data)

    {
        "type": "batch",
        "batch_id": "<batch id>",
        "cases": [
            "<list of case data>"
        ],
        "points": "<batch points awarded>",
        "total": "<batch total points>"
    }

### [`/api/v2/organizations`](#/site/api?id=apiv2organizations)

Example: [/api/v2/organizations?is\_open=False](https://dmoj.ca/api/v2/organizations?is_open=False)

#### [Basic filters](#/site/api?id=basic-filters-4)

*   `is_open` - boolean

#### [List filters](#/site/api?id=list-filters-4)

*   `id` - organization id

#### [Object response](#/site/api?id=object-response-9)

    {
        "id": "<organization id>",
        "slug": "<organization slug>",
        "short_name": "<organization name>",
        "is_open": "<whether anyone can join the organization>",
        "member_count": "<number of users in the organization>"
    }

### [`/api/v2/languages`](#/site/api?id=apiv2languages)

Example: [/api/v2/languages?common\_name=Python](https://dmoj.ca/api/v2/languages?common_name=Python)

#### [Basic filters](#/site/api?id=basic-filters-5)

*   `common_name` - language common name

#### [List filters](#/site/api?id=list-filters-5)

*   `id` - language id
*   `key` - language key

#### [Object response](#/site/api?id=object-response-10)

    {
        "id": "<language id>",
        "key": "<language key>",
        "short_name": "<language short name>",
        "common_name": "<language common name>",
        "ace_mode_name": "<Ace mode name>",
        "pygments_name": "<Pygments name>",
        "code_template": "<default code template>"
    }

### [`/api/v2/judges`](#/site/api?id=apiv2judges)

Example: [/api/v2/judges](https://dmoj.ca/api/v2/judges)

#### [Object response](#/site/api?id=object-response-11)

    {
        "name": "<judge name>",
        "start_time": "<judge start time in ISO format>",
        "ping": "<judge ping in milliseconds>",
        "load": "<judge load>",
        "languages": [
            "<list of language key>"
        ]
    }