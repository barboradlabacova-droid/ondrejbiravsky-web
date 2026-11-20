// Zámek na náhled webu (heslo), funguje i na bezplatném Netlify.
// Zapíná se proměnnou NAHLED_HESLO v Netlify (Site configuration → Environment variables).
// Když proměnná není nastavená, web je normálně veřejný.
// Při spuštění ostrého webu tento soubor smažte, ať se zbytečně nevolá.
export default async (request, context) => {
  const heslo = (Netlify.env.get("NAHLED_HESLO") || "").trim();
  if (!heslo) return context.next();
  const auth = request.headers.get("authorization") || "";
  if (auth.startsWith("Basic ")) {
    try {
      const [jmeno = "", zadane = ""] = atob(auth.slice(6)).split(/:(.*)/s);
      // heslo stačí napsat do kteréhokoli pole (jméno i heslo)
      if (zadane.trim() === heslo || jmeno.trim() === heslo) {
        const res = await context.next();
        res.headers.set("X-Robots-Tag", "noindex, nofollow");
        return res;
      }
    } catch (_) { /* špatná hlavička → zamčeno */ }
  }
  return new Response("Náhled webu je zamčený.", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="Nahled webu", charset="UTF-8"',
      "Content-Type": "text/plain; charset=utf-8",
      "X-Robots-Tag": "noindex, nofollow",
    },
  });
};

export const config = { path: "/*", excludedPath: ["/.netlify/*"] };
