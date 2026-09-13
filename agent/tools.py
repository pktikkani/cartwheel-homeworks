"""Homework 1: the remaining commerce-agent tools.

The three lecture tools (`search_help_center`, `get_order`, `issue_refund`)
are implemented in agent/agent.py and are worked examples of the pattern:
check permissions first, go through agent/db.py for data, and return a
structured dict, never a prose error. The homework tools follow the same
pattern. agent/agent.py already wraps each function below as an SDK tool, so
once a function works here it works in chat with no further wiring.

Result convention (see agent/auth.py):
  - Success: a dict with "ok": True plus the payload fields named in each
    docstring.
  - Failure: {"ok": False, "error": <code>, "reason": <human-readable str>}.

Run the contract tests with: uv run pytest tests/test_hw_holes.py -k hw1
They are marked xfail and flip to passing as you implement each function.
"""

from __future__ import annotations

from operator import itemgetter
from typing import Any, List

from agent import db
from agent.auth import AuthContext, can_cancel_order, permission_denied
from agent.helpcenter import load_policy_docs, PolicyDoc
from agent.killswitch import kill_switch

MAX_SEARCH_LIMIT = 25
DEFAULT_ORDER_LIMIT = 20


def get_policy(ctx: AuthContext, policy_id: str) -> dict[str, Any]:
    """Fetch one policy doc by its exact id. Risk tier: read.

    Every role may read every policy doc (the corpus is public help-center
    content), so this tool needs no permission check.

    Args:
        ctx: The caller's auth context. Unused here, but every tool takes it.
        policy_id: An exact policy id, e.g. "cw-returns" or
            "store-juniper-home-goods-policy". Matching is exact and
            case-sensitive; ids are the `policy_id` front-matter field of the
            files in data/policies/.

    Returns:
        On success: {"ok": True, "policy_id": str, "title": str,
        "audience": str, "body": str} where body is the markdown body of the
        doc without the front matter.
        If no doc has that id: {"ok": False, "error": "not_found",
        "reason": ...} naming the id that was requested.

    Implementation notes:
        agent.helpcenter.load_policy_docs() returns every parsed doc.
    """

    policy_docs: List[PolicyDoc] = load_policy_docs()

    policy_doc = (policy_doc for policy_doc in policy_docs if policy_doc.policy_id == policy_id)
    matched_policy_doc = next(policy_doc, None)
    if matched_policy_doc is not None:
        return {"ok": True, "policy_id": matched_policy_doc.policy_id, "title": matched_policy_doc.title , "audience": matched_policy_doc.audience, "body": matched_policy_doc.body}
    else:
        return {"ok": False, "error": "not_found", "reason": f"{policy_id} Not Found"}



def search_products(
    ctx: AuthContext,
    query: str,
    store: str | None = None,
    max_price_usd: float | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Search the product catalog. Risk tier: read.

    Every role may search products. Matching is deterministic keyword
    matching, not semantic search: a product matches when every whitespace
    token of `query` appears case-insensitively as a substring of the
    product's title or description.

    Args:
        ctx: The caller's auth context.
        query: Free-text query. Must be non-empty after stripping whitespace;
            otherwise return {"ok": False, "error": "invalid_argument",
            "reason": ...}.
        store: Optional store filter. Matched with
            agent.db.get_store_by_name (case-insensitive name or slug). If
            given and no store matches, return {"ok": False, "error":
            "not_found", "reason": ...} naming the store string.
        max_price_usd: Optional inclusive price ceiling. If given and not
            strictly positive, return an "invalid_argument" error.
        limit: Maximum products to return. Clamp to the range
            [1, MAX_SEARCH_LIMIT]; do not error on out-of-range values.

    Returns:
        {"ok": True, "products": [...], "count": <len(products)>} where each
        product is {"product_id": int, "store_id": int, "title": str,
        "price_usd": float}. Sort matches by price_usd ascending, then by
        product_id ascending, and truncate to `limit`. No matches is still a
        success: {"ok": True, "products": [], "count": 0}.

    Implementation notes:
        agent.db.list_products(conn, store_id) gives the candidate set.
        Use `with db.connection() as conn:` to close the database automatically.
    """

    if not query.strip():
        return {"ok": False, "error": "invalid_argument", "reason": f"{query} is empty"}
    if max_price_usd is not None and max_price_usd <= 0  :
        return {"ok": False,"error": "invalid_argument", "reason": f"{max_price_usd} must be positive"}

    limit = max(1, min(limit, MAX_SEARCH_LIMIT))

    with db.connection() as conn:
        store_id = None
        if store is not None:
            store_found = db.get_store_by_name(conn, store)
            if store_found is None:
                return {"ok": False, "error": "not_found", "reason": f"{store} Not Found"}
            store_id = store_found.id
        products_returned = db.list_products(conn, store_id=store_id)

    tokens = query.lower().split()
    product_found = [product for product in products_returned
                     if all(token in product.title.lower() or token in product.description.lower() for token in tokens)
                     and (max_price_usd is None or product.price_usd <= max_price_usd) ]


    limited_sorted_products = sorted(product_found, key= lambda sorted_product: (sorted_product.price_usd, sorted_product.id))[:limit]
    products = [{"title": product.title, "product_id": product.id, "store_id": product.store_id, "price_usd": product.price_usd} for product in limited_sorted_products]

    return {"ok": True, "products": products, "count": len(products)}

def list_my_orders(ctx: AuthContext) -> dict[str, Any]:
    """List recent orders in the caller's own scope. Risk tier: read.

    Role behavior, straight from the access matrix in SPEC.md:
        - shopper: the caller's own orders.
        - merchant: the caller's store's orders (ctx.store_id).
        - support: support staff have no orders of their own and look up
          specific orders with get_order instead, so return {"ok": False,
          "error": "invalid_argument", "reason": ...} saying exactly that.

    Returns:
        For shopper and merchant: {"ok": True, "orders": [...],
        "count": <len(orders)>} where each order is
        agent.db.Order.to_public_dict() and the list holds at most
        DEFAULT_ORDER_LIMIT orders, newest first (agent.db.list_orders_for_user
        and list_orders_for_store already sort and limit this way).

    Implementation notes:
        No permission check is needed beyond the role dispatch, because the
        scope is baked into which query you run. That is the point of the
        tool: the model cannot ask for someone else's orders through it.
    """

    if ctx.role == "support":
        return {
            "ok": False,
            "error": "invalid_argument",
            "reason": "Support staff have no personal orders; use get_order instead",
        }

    with db.connection() as conn:
        if ctx.role == "shopper":
            orders = db.list_orders_for_user(conn, ctx.user_id)



        elif ctx.role == "merchant":
            if ctx.store_id is None:
                return {"ok": False, "error": "invalid_argument", "reason": "Merchant account is missing a store ID."}
            orders = db.list_orders_for_store(conn, ctx.store_id)

        public_orders = [order.to_public_dict() for order in orders]


    return {"ok": True, "orders": public_orders, "count": len(public_orders)}


def cancel_order(ctx: AuthContext, order_id: int, reason: str) -> dict[str, Any]:
    """Cancel an order. Risk tier: write.

    This is the homework's write tool, and it must enforce two independent
    rules in this order:

    1. The access matrix (scope): use agent.auth.can_cancel_order. Shoppers
       may cancel only their own orders, merchants only their own store's
       orders, support any order. On failure return
       agent.auth.permission_denied(...) with a reason naming the role and
       the order id. Scope is checked before the status rule so that an
       out-of-scope caller learns nothing about the order's state.
    2. The pre-shipment rule (facts.yaml `cancel_cutoff`): only orders whose
       status is exactly "placed" can be cancelled, for every role. If the
       order is in scope but its status is not "placed", return
       {"ok": False, "error": "not_eligible", "reason": ...} that names the
       current status and states that orders can be cancelled only before
       shipment.

    Args:
        ctx: The caller's auth context.
        order_id: The order to cancel.
        reason: Free-text reason from the user; not validated.

    Returns:
        If no order has this id: {"ok": False, "error": "not_found",
        "reason": ...}.
        On success: {"ok": True, "order_id": order_id, "status": "cancelled"}
        after persisting the new status with agent.db.set_order_status.

    Implementation notes:
        Fetch with agent.db.get_order. Note the argument order of
        can_cancel_order(ctx, order_user_id, order_store_id).

    The Module 4 kill switch is checked first (before the scope and
    status rules and before your code), so that a paused write tool touches
    nothing. It is provided; the default ("off") returns None and falls
    through to your implementation.
    """
    paused = kill_switch("cancel_order")
    if paused is not None:
        return {"ok": False, "error": "paused", "reason": paused}

    with db.connection() as conn:
        order = db.get_order(conn, order_id)
        if order is None:
            return {"ok": False, "error": "not_found", "reason": f"Order with id {order_id} not found"}
        if not can_cancel_order(ctx, order.user_id, order.store_id):
            return permission_denied(f"{ctx.role} cannot cancel order {order_id}")
        if order.status == "placed":
            db.set_order_status(conn, order_id, "cancelled")
        else:
            return {"ok": False, "error": "not_eligible", "reason": f"Order with id {order_id} has status {order.status}; "
                                                                    f"orders can be cancelled only before shipment"}


        return {"ok": True, "order_id": order_id, "status": "cancelled"}



def find_order(ctx: AuthContext, query: str) -> dict[str, Any]:
    """Search the caller's orders by product name. Risk tier: read.

    Takes a natural-language query (e.g., "earmuffs I bought last week")
    and searches the authenticated user's orders for products whose name
    matches. Use fuzzy string matching (e.g., thefuzz.fuzz.partial_ratio
    or case-insensitive substring matching) to find orders whose product name is close to the
    query.

    Access rules: a shopper searches only the shopper's own orders, a
    merchant searches orders from the merchant's store, and support staff
    can search any orders. Use agent.db.list_order_search_candidates with
    user_id=ctx.user_id for shoppers, store_id=ctx.store_id for merchants,
    or all_orders=True only for support. Derive the scope from ctx, never
    from the query; reject unsupported roles or missing required identity.
    Use agent.db.list_products to map product IDs to product titles.

    The helper returns the complete authorised scope, newest first with
    order ID descending as the tie-breaker. Match product names first,
    preserve that order, then return at most five matches. Do not search
    only the 20 most recent orders. Convert matches with to_public_dict().

    Args:
        ctx: The caller's auth context.
        query: A natural-language description of the product.

    Returns:
        {"ok": True, "orders": [...]} with a list of matching orders
        (at most 5), each as the dict returned by agent.db. If no orders
        match, return {"ok": True, "orders": []}.
    """

    with db.connection() as conn:
        if ctx.role == "shopper":
            candidate_orders = db.list_order_search_candidates(conn, user_id=ctx.user_id)
        elif ctx.role == "merchant":
            if ctx.store_id is None:
                return {"ok": False, "error": "invalid_argument", "reason": "Merchant account is missing a store ID."}
            candidate_orders = db.list_order_search_candidates(conn, store_id=ctx.store_id)
        elif ctx.role == "support":
            candidate_orders = db.list_order_search_candidates(conn, all_orders=True)
        else:
            return {"ok": False, "error": "invalid_argument", "reason": f"Unsupported role: {ctx.role}"}

        products = db.list_products(conn)
        product_titles = {product.id: product.title for product in products}
        normalized_query = query.lower()
        matching_orders = []
        for order in candidate_orders:
            title = product_titles.get(order.product_id, "")
            normalized_title = title.lower()
            if normalized_title and (normalized_title in normalized_query or normalized_query in normalized_title):
                matching_orders.append(order)

        public_orders = [order.to_public_dict() for order in matching_orders[:5]]

        return {"ok": True, "orders": public_orders}


def get_store_info(ctx: AuthContext, store: str) -> dict[str, Any]:
    """Look up authoritative public information for a store.

    Args:
        ctx: Authenticated request context.
        store: Exact store name or slug. Must not be empty.

    Returns:
        On success, the store ID, name, slug, category,
        return-window override, and restocking-fee setting.
        Returns "invalid_argument" for an empty store value and
        "not_found" when no matching store exists.
    """

    store_name = store.strip()
    if not store_name:
        return {"ok": False, "error": "invalid_argument", "reason": "store must not be empty"}

    with db.connection() as conn:
        found = db.get_store_by_name(conn, store_name)
        if found is None:
            return {"ok": False, "error": "not_found", "reason": f"store '{store_name}' does not exist"}

    return {
        "ok": True,
        "store": {
            "store_id": found.id,
            "name": found.name,
            "slug": found.slug,
            "category": found.category,
            "return_window_days_override": found.return_window_days_override,
            "restocking_fee_opt_in": found.restocking_fee_opt_in,
        },
    }
