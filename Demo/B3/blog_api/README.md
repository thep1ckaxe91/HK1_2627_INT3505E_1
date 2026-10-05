### Sơ đồ cây endpoint & resources trong domain

Các resource là:
- user 
- post
- comment
- tag
- follow (follower/following)

![API resource tree](<API resource tree.png>)

### Route cho collection /posts

| Entity  | Collection URI              | Item URI               | Sub-resource URI & Context                            |
| ------- | --------------------------- | ---------------------- | ----------------------------------------------------- |
| Post    | /posts                      | /posts/{post_id}       | /users/{user_id}/posts (posts by author)              |
| Comment | — (rarely queried globally) | /comments/{comment_id} | /posts/{post_id}/comments (comments on post)          |
| User    | /users                      | /users/{user_id}       | /users/{user_id}/profile                              |
| Tag     | /tags                       | /tags/{tag_id}         | /posts/{post_id}/tags (tags assigned to post)         |
| Follow  | —                           | —                      | /users/{user_id}/followers /users/{user_id}/following |

