# Deploying the site

The hosted site is the repository itself, served as static files, plus one small function for the email sign-up.
[Cloudflare Pages](https://pages.cloudflare.com/) does both on its free plan, with no build step.

Students still run code on their own machines with `python tools/serve.py`. The hosted site is for reading the
lessons, taking the quizzes, seeing exercise hints and answers, and joining the email list.

## Before the first deploy

1. Check that the GitHub links in `index.html` and `README.md` point at your repository.
2. Regenerate and check:
   ```
   python tools/build_static.py      # exercise data for pages without the runner
   python tools/build_helpers.py     # the test guides
   python tools/design_lint.py       # design and copy rules
   ```
3. Commit, and push the repository to GitHub.

## Cloudflare Pages

1. In the Cloudflare dashboard, open **Workers & Pages**, choose **Create**, then **Pages**, then **Connect to Git**,
   and pick the repository.
2. Build settings: framework preset **None**, build command empty, build output directory `/`.
3. Deploy. The site is live at `<project>.pages.dev`. `index.html` is the landing page, `/site/` is the course, and
   `functions/api/subscribe.js` becomes `/api/subscribe`.
4. Under the project's **Custom domains**, add your domain. If the domain's DNS is on Cloudflare, it sets up the
   record and the certificate for you.

Every push to the main branch deploys again. Other branches get preview URLs.

`_headers` sets a few security headers and serves the specs and tests as plain text. `404.html` is the page for
links that don't exist.

### Limit sign-up abuse

The function emails nobody at sign-up, so the worst a bot can do is add junk addresses. To cap that, add a free
rate-limiting rule under **Security**, then **WAF**, for the path `/api/subscribe` (for example, 5 requests per 10
seconds per IP).

## The email list (Resend)

Sign-ups go to [Resend](https://resend.com) contacts, the same email service Behavior uses.

1. Create a Resend account, and an API key with access to contacts.
2. Optional: create a segment named "Course updates" and copy its id, so course sign-ups stay apart from anything else
   in the account.
3. In the Pages project, under **Settings**, then **Variables and Secrets**, add:

   | name | value |
   |---|---|
   | `RESEND_API_KEY` | the key, as a secret |
   | `RESEND_SEGMENT_ID` | the segment id (optional) |

4. Deploy again so the function sees them, then sign up once on the live site and check that the contact appears.

To announce a new week, send a **broadcast** to the segment from Resend. Broadcasts need a verified sending domain
(Resend walks you through the DNS records) and carry an unsubscribe link. A US mailing also needs a postal address in
the email (CAN-SPAM).

Until the variables are set, the form answers "Sign-up is not set up yet." On the local runner it says sign-up works
on the hosted site.

## Costs

Cloudflare Pages is free for this: static files are unlimited, and the free plan's function requests are far above
what a sign-up form needs. Resend has a free tier for sending and for contacts. Check its current limits on its
pricing page before the list grows large. The only fixed cost is the domain.
