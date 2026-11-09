// POST /api/subscribe: adds an email to the course's Resend contacts, for "new week" announcements.
// A Cloudflare Pages Function (deployed with the site, see DEPLOY.md). Settings, in the Pages project's environment:
//   RESEND_API_KEY      a Resend key that can manage contacts (Full access, or Sending + contacts)
//   RESEND_SEGMENT_ID   optional: the segment new contacts join, so course sign-ups stay apart from anything else
// Nothing is emailed at sign-up, so the form can't be used to send mail to strangers. Announcements go out later as
// Resend broadcasts, which carry an unsubscribe link.
const json = (status, body) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } })

export async function onRequest({ request, env }) {
  if (request.method !== 'POST') return json(405, { error: 'Use POST.' })
  // Only the site's own pages: a cross-site form post has another Origin
  const origin = request.headers.get('Origin')
  if (origin && origin !== new URL(request.url).origin) return json(403, { error: 'Sign up from the course site.' })
  let body
  try { body = await request.json() } catch { return json(400, { error: 'That did not go through. Try again.' }) }
  // The hidden field is filled only by bots. Answer as if it worked, so they learn nothing.
  if (body.website) return json(200, { ok: true })
  const email = String(body.email || '').trim().toLowerCase()
  if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return json(400, { error: 'That email looks incomplete.' })
  if (!env.RESEND_API_KEY) return json(503, { error: 'Sign-up is not set up yet. Try again soon.' })

  const contact = { email, unsubscribed: false, ...(env.RESEND_SEGMENT_ID ? { segments: [{ id: env.RESEND_SEGMENT_ID }] } : {}) }
  let res
  try {
    res = await fetch('https://api.resend.com/contacts', {
      method: 'POST', headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(contact),
    })
  } catch { return json(502, { error: 'That did not go through. Try again in a minute.' }) }
  // Signing up twice is fine: the person is on the list either way, so say so.
  if (res.ok || res.status === 409) return json(200, { ok: true })
  console.error('Resend contact failed', res.status, await res.text().catch(() => ''))
  return json(502, { error: 'That did not go through. Try again in a minute.' })
}
