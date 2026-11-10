/**
 * Cloudflare Workers Static Assets Gateway
 * Automatically routes all incoming edge traffic to static site assets in ./public.
 */

interface Env {
	ASSETS: {
		fetch: (request: Request | string) => Promise<Response>;
	};
}

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		const url = new URL(request.url);

		// Optional edge health check endpoint
		if (url.pathname === '/api/health') {
			return new Response(JSON.stringify({ status: 'ok', worker: 'pSEO Static Edge' }), {
				status: 200,
				headers: {
					'Content-Type': 'application/json',
					'Cache-Control': 'no-store',
				},
			});
		}

		// Delegate all other requests to Cloudflare Workers Static Assets binding
		return env.ASSETS.fetch(request);
	},
};
