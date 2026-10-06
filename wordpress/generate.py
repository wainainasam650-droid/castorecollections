"""Generate Elementor JSON (flexbox containers) for the Castore Collection Kenya site.

Run:  python3 wordpress/generate.py   -> writes wordpress/build/*.json
Tokens replaced on the server when the JSON is imported:
  __MEGA_ID__, __DRAWER_ID__  popup template ids
Styling lives in castore-site.css; elements only carry class names (css_classes).
"""
import hashlib
import json
import os
import re
from urllib.parse import quote

OUT = os.path.join(os.path.dirname(__file__), "build")
_n = 0

UP = "https://castorecollections.co.ke/wp-content/uploads/"
IMG = {
    "logo": (425, UP + "2026/09/cropped-Screenshot_2026-09-21_172206-removebg-preview.png"),
    "kitchen": (468, UP + "2026/10/kitchen-hero.jpg"),
    "dishrack": (469, UP + "2026/10/dish-rack.jpg"),
    "plates": (402, UP + "2026/09/c03b543b54ccca179067b9d10f3975c0.jpg"),
    "seat_room": (444, UP + "2026/09/d8cda7eff85d379bb87b287fb2faabaa.jpg"),
}

CATS = [
    ("Kitchen & Dining", ["Cookware & Pots", "Pressure Cookers", "Utensils & Gadgets", "Knives & Chopping Boards", "Food Storage Containers", "Dinnerware & Plates", "Cups, Mugs & Glasses", "Flasks & Water Bottles", "Bakeware", "Tea & Serving Sets", "Kitchen Racks & Holders", "Lunch Boxes"]),
    ("Kitchen Appliances", ["Blenders & Juicers", "Electric Kettles", "Air Fryers", "Rice Cookers", "Toasters & Sandwich Makers", "Microwaves", "Coffee Makers", "Hand Mixers", "Cookers & Hot Plates"]),
    ("Water Dispensers & Filters", ["Hot & Cold Dispensers", "Bottom-Load Dispensers", "Tabletop Dispensers", "Water Pumps", "Water Filters & Purifiers", "Dispenser Bottles"]),
    ("Home Decor", ["Wall Art & Clocks", "Mirrors", "Vases & Artificial Plants", "Candles & Scents", "Cushions & Throws", "Rugs & Carpets", "Curtains", "Lamps & Lighting", "Photo Frames", "Table Decor"]),
    ("Furniture & Seating", ["Inflatable Seats & Sofas", "Stools & Chairs", "Side & Coffee Tables", "Shoe Racks", "Shelves", "Folding Furniture"]),
    ("Bedding", ["Bedsheets", "Duvets & Comforters", "Blankets", "Pillows", "Mattress Protectors", "Mosquito Nets", "Bedspreads"]),
    ("Bathroom", ["Towels", "Bath Mats", "Bathroom Organisers", "Shower Accessories", "Toilet Accessories", "Soap Dispensers"]),
    ("Cleaning & Laundry", ["Mops & Brooms", "Buckets & Basins", "Laundry Baskets", "Drying Racks", "Cleaning Tools", "Dustbins"]),
    ("Storage & Organisation", ["Storage Boxes", "Wardrobe Organisers", "Hangers", "Under-Bed Storage", "Drawer Organisers", "Hooks & Wall Storage"]),
    ("Home Appliances", ["Irons", "Fans", "Vacuum Cleaners", "Heaters", "Extension Cables"]),
    ("Deals", ["Flash Sale", "Clearance", "Bundles & Sets", "New Arrivals"]),
]
CAT_IDS = {"Kitchen & Dining": 19, "Home Decor": 21}
TILE_SUBS = {
    "Kitchen & Dining": "Cookware & Pots, Pressure Cookers, Utensils & Gadgets",
    "Kitchen Appliances": "Blenders & Juicers, Electric Kettles, Air Fryers",
    "Water Dispensers & Filters": "Hot & Cold Dispensers, Water Pumps, Water Filters & Purifiers",
    "Home Decor": "Wall Art & Clocks, Mirrors, Cushions & Throws",
    "Furniture & Seating": "Inflatable Seats & Sofas, Stools & Chairs, Shoe Racks",
    "Bedding": "Bedsheets, Duvets & Comforters, Blankets, Pillows",
    "Bathroom": "Towels, Bath Mats, Bathroom Organisers",
    "Cleaning & Laundry": "Mops & Brooms, Laundry Baskets, Drying Racks",
    "Storage & Organisation": "Storage Boxes, Wardrobe Organisers, Hangers",
    "Home Appliances": "Irons, Fans, Vacuum Cleaners, Heaters",
}
TILE_PHOTO = {"Kitchen & Dining": "plates", "Furniture & Seating": "seat_room"}
POLICIES = [("Delivery information", "/delivery-information/"), ("Returns and refunds", "/returns-and-refunds/"), ("Privacy policy", "/privacy-policy/"), ("Terms and conditions", "/terms-and-conditions/")]


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower().replace("&", "")).strip("-")


def cat_url(main, sub=None):
    return "/product-category/" + slug(main) + "/" + (slug(sub) + "/" if sub else "")


def rid():
    global _n
    _n += 1
    return hashlib.md5(f"castore-{_n}".encode()).hexdigest()[:7]


def link(url):
    return {"url": url, "is_external": "", "nofollow": "", "custom_attributes": ""}


def icon(value, library="fa-solid"):
    return {"value": value, "library": library}


# ---------- element helpers ----------
def con(cls, children=(), tag=None, url=None, inner=True):
    s = {"content_width": "full", "css_classes": cls}
    if tag:
        s["html_tag"] = tag
    if url:
        s["html_tag"] = "a"
        s["link"] = link(url)
    return {"id": rid(), "elType": "container", "isInner": inner, "settings": s, "elements": list(children)}


def section(cls, children, tag="section"):
    return con(cls, children, tag=tag, inner=False)


def widget(wtype, settings, cls=""):
    if cls:
        settings["_css_classes"] = cls
    return {"id": rid(), "elType": "widget", "widgetType": wtype, "settings": settings, "elements": []}


def heading(text, cls, tag="h2", url=None):
    s = {"title": text, "header_size": tag}
    if url:
        s["link"] = link(url)
    return widget("heading", s, cls)


def text(html, cls):
    return widget("text-editor", {"editor": html}, cls)


def button(label, url, cls, ico=None, dynamic_popup=None):
    s = {"text": label, "link": link(url)}
    if ico:
        s["selected_icon"] = ico
        s["icon_align"] = "row"
    if dynamic_popup:
        action = "toggle" if dynamic_popup == "__MEGA_ID__" else "open"
        tag_settings = quote(json.dumps({"popup": dynamic_popup, "action": action}, separators=(",", ":")))
        s["__dynamic__"] = {"link": f'[elementor-tag id="{rid()}" name="popup" settings="{tag_settings}"]'}
        s["link"] = link("")
    return widget("button", s, cls)


def image(key, cls, url=None, size="large"):
    s = {"image": {"id": IMG[key][0], "url": IMG[key][1]}, "image_size": size}
    if url:
        s["link_to"] = "custom"
        s["link"] = link(url)
    return widget("image", s, cls)


def placeholder(label, cls=""):
    return con(("image-placeholder " + cls).strip(), [heading(label, "image-placeholder-label", "p")])


def icon_box(ico, title, desc, cls, url=None):
    s = {"selected_icon": ico, "title_text": title, "description_text": desc, "position": "inline-start", "title_size": "h3"}
    if url:
        s["link"] = link(url)
    return widget("icon-box", s, cls)


def icon_widget(ico, cls, url=None, label=""):
    s = {"selected_icon": ico, "view": "default"}
    if url:
        s["link"] = link(url)
        if label:
            s["link"]["custom_attributes"] = "aria-label|" + label
    return widget("icon", s, cls)


def link_list(items, cls, ico=None):
    rows = []
    for item in items:
        label, url = item[0], item[1]
        row = {"_id": rid(), "text": label, "selected_icon": ico or {"value": "", "library": ""}, "link": link(url)}
        rows.append(row)
    return widget("icon-list", {"icon_list": rows, "view": "traditional"}, cls)


def tick_list(labels):
    rows = [{"_id": rid(), "text": t, "selected_icon": icon("fas fa-check")} for t in labels]
    return widget("icon-list", {"icon_list": rows, "view": "traditional", "space_between": {"unit": "px", "size": 0}}, "tick-list")


def products(cls, query, columns=4, rows=1):
    s = {"columns": columns, "columns_tablet": 3, "columns_mobile": 2, "rows": rows, "paginate": "", "query_post_type": "product", "query_orderby": "date", "query_order": "desc"}
    s.update(query)
    return widget("woocommerce-products", s, cls)


def wrap(children, extra=""):
    return con(("wrap " + extra).strip(), children)


def section_head(title, link_label=None, url=None):
    kids = [heading(title, "section-heading", "h2")]
    if link_label:
        kids.append(heading(link_label, "text-link", "p", url))
    return con("section-head", kids)


# =========================================================
# HEADER (theme builder: header)
# =========================================================
def header():
    announcement = section("announcement-bar", [
        text("Free delivery within Nairobi on orders over KSh [AMOUNT]", "announcement-item"),
        con("announcement-dot announcement-extra"),
        text("Pay with M-Pesa on checkout", "announcement-item announcement-extra"),
        con("announcement-dot announcement-extra"),
        text("New arrivals every week", "announcement-item announcement-extra"),
    ], tag="div")
    cart = widget("woocommerce-menu-cart", {"icon": "bag-medium", "items_indicator": "plain", "show_subtotal": "", "cart_type": "side-cart", "hide_empty_indicator": ""}, "header-cart")
    main = section("header-main", [wrap([
        image("logo", "logo", "/", "full"),
        widget("wp-widget-woocommerce_product_search", {"wp": {"title": ""}}, "search-bar"),
        icon_box(icon("fas fa-box"), "Track your order", "Where is my parcel?", "track-link", "/track-your-order/"),
        con("header-icons", [
            icon_widget(icon("far fa-user", "fa-regular"), "header-icon", "/my-account/", "My account"),
            cart,
        ]),
    ], "header-main-inner")], tag="div")
    menu = section("header-menu", [wrap([
        button("All Categories", "#", "menu-trigger", icon("fas fa-bars"), dynamic_popup="__MEGA_ID__"),
        widget("nav-menu", {"menu": "main-menu", "layout": "horizontal", "submenu_icon": {"value": "", "library": ""}, "toggle": "", "dropdown": "none"}, "menu-links"),
        widget("nav-menu", {"menu": "secondary-menu", "layout": "horizontal", "toggle": "", "dropdown": "none"}, "menu-links-secondary"),
    ], "header-menu-inner")], tag="nav")
    compact = section("header-compact", [wrap([
        button("Menu", "#", "menu-button", icon("fas fa-bars"), dynamic_popup="__DRAWER_ID__"),
        image("logo", "logo", "/", "full"),
        widget("search-form", {"skin": "full_screen", "placeholder": "Search for cookware, dispensers, decor…", "toggle_align": "end"}, "search-toggle"),
        widget("woocommerce-menu-cart", {"icon": "bag-medium", "items_indicator": "plain", "show_subtotal": "", "cart_type": "side-cart", "hide_empty_indicator": ""}, "header-cart"),
    ], "header-compact-inner")], tag="div")
    return [announcement, main, menu, compact]


# =========================================================
# MEGA MENU (popup) + MOBILE DRAWER (popup)
# =========================================================
def mega():
    tabs, panels = [], []
    for name, subs in CATS:
        tabs.append({"_id": rid(), "tab_title": name})
        promo = con("mega-promo", [
            heading("Featured", "eyebrow-light", "p"),
            heading(f"[Featured promo for {name}]", "promo-box-title", "p"),
            heading("Shop now", "promo-box-link", "p", cat_url(name)),
        ])
        panels.append(con("mega-panel", [
            con("mega-links", [
                con("section-head", [heading(name, "heading-card", "h3"), heading(f"Shop all {name}", "text-link", "p", cat_url(name))]),
                link_list([(s, cat_url(name, s)) for s in subs], "link-list mega-sublist"),
            ]),
            promo,
        ]))
    tabs_widget = widget("nested-tabs", {"tabs": tabs, "tabs_direction": "inline-start", "breakpoint_selector": "none"}, "mega-tabs")
    tabs_widget["elType"] = "widget"
    tabs_widget["elements"] = panels
    return [section("mega-menu", [tabs_widget], tag="div")]


def drawer():
    items, panels = [], []
    for name, subs in CATS:
        items.append({"_id": rid(), "item_title": name})
        panels.append(con("drawer-subs", [link_list([(s, cat_url(name, s)) for s in subs] + [(f"Shop all {name}", cat_url(name))], "link-list")]))
    acc = widget("nested-accordion", {"items": items, "default_state": "all_collapsed", "max_items_expended": "one", "title_tag": "div",
                                      "accordion_item_title_icon": icon("fas fa-plus"), "accordion_item_title_icon_active": icon("fas fa-minus")}, "drawer-cats")
    acc["elements"] = panels
    return [section("drawer", [
        con("drawer-top", [image("logo", "logo", "/", "full")]),
        icon_box(icon("fas fa-box"), "Track your order", "Where is my parcel?", "track-link drawer-track", "/track-your-order/"),
        heading("All Categories", "drawer-label", "p"),
        acc,
        heading("Shop", "drawer-label", "p"),
        link_list([("Shop All", "/shop/"), ("New Arrivals", cat_url("Deals", "New Arrivals")), ("Best Sellers", "/shop/?orderby=popularity"), ("Sale", cat_url("Deals"))], "link-list drawer-links"),
        heading("Help", "drawer-label", "p"),
        link_list([("About", "/about/"), ("Contact", "/contact/"), ("FAQ", "/faq/"), ("My account", "/my-account/")], "link-list drawer-links"),
    ], tag="div")]


# =========================================================
# FOOTER (theme builder: footer) + floating WhatsApp button
# =========================================================
def footer():
    social = widget("social-icons", {"social_icon_list": [
        {"_id": rid(), "social_icon": icon("fab fa-facebook-f", "fa-brands"), "link": link("[FACEBOOK URL]")},
        {"_id": rid(), "social_icon": icon("fab fa-instagram", "fa-brands"), "link": link("[INSTAGRAM URL]")},
        {"_id": rid(), "social_icon": icon("fab fa-tiktok", "fa-brands"), "link": link("[TIKTOK URL]")},
    ], "shape": "circle"}, "footer-social")
    cols = con("footer-cols", [
        con("footer-brand", [
            image("logo", "logo-light", "/", "full"),
            text("Quality household goods for Kenyan homes", "body-text-light"),
            social,
        ]),
        con("footer-col", [heading("Shop", "footer-title", "h2"), link_list([(n, cat_url(n)) for n, _ in CATS[:5]] + [("All categories", "/shop/"), ("Sale", cat_url("Deals"))], "link-list")]),
        con("footer-col", [heading("Help", "footer-title", "h2"), link_list([("FAQ", "/faq/"), ("Track my order", "/track-your-order/"), ("My account", "/my-account/"), ("Contact us", "/contact/")], "link-list")]),
        con("footer-col", [heading("Policies", "footer-title", "h2"), link_list(POLICIES, "link-list")]),
        con("footer-col", [heading("Contact", "footer-title", "h2"), link_list([
            ("[PHONE / WHATSAPP]", "/whatsapp/"), ("[EMAIL]", "/contact/"), ("[LOCATION], Kenya", "/contact/"),
        ], "link-list")]),
    ])
    bottom = con("footer-bottom", [
        text("© 2026 Castore Collection Kenya", "footer-small"),
        text("We accept M-Pesa", "footer-small"),
    ])
    float_btn = button("Chat with us\non WhatsApp", "/whatsapp/", "whatsapp-float", icon("fab fa-whatsapp", "fa-brands"))
    return [section("site-footer band", [wrap([cols, bottom])], tag="footer"), float_btn]


# =========================================================
# HOME
# =========================================================
def home():
    hero = section("band-hero", [wrap([
        con("hero-copy", [
            heading("Household essentials, delivered", "eyebrow", "p"),
            heading("Better products. Better living.", "heading-hero", "h1"),
            text("Quality kitchenware, home decor and water dispensers for Kenyan homes, at fair prices, with delivery to your door.", "lead"),
            button("Shop now", "/shop/", "button-primary"),
            tick_list(["Pay with M-Pesa", "Countrywide delivery"]),
        ]),
        con("hero-media", [
            con("hero-photo-tall", [image("kitchen", "photo", None, "large")]),
            con("hero-side", [
                con("hero-photo-small", [image("dishrack", "photo", None, "large")]),
                con("promo-box", [
                    heading("This week", "eyebrow-light", "p"),
                    heading("Up to 25% off selected items", "promo-box-title", "p"),
                    heading("See the deals", "promo-box-link", "p", cat_url("Deals")),
                ]),
            ]),
        ]),
    ], "hero")])
    trust = section("band band-tight", [wrap([con("trust-strip", [
        icon_box(icon("fas fa-mobile-alt"), "Pay with M-Pesa", "Pay on checkout", "trust-item"),
        icon_box(icon("fas fa-truck"), "Fast delivery", "Nairobi in [X] days, countrywide in [X] days", "trust-item"),
        icon_box(icon("fas fa-check-circle"), "Quality checked", "[How you check products]", "trust-item"),
        icon_box(icon("fab fa-whatsapp", "fa-brands"), "WhatsApp support", "[PHONE NUMBER]", "trust-item", "/whatsapp/"),
    ])])])
    tiles = []
    for name, _ in CATS[:10]:
        media = con("photo-frame", [image(TILE_PHOTO[name], "photo", None, "medium_large")]) if name in TILE_PHOTO else placeholder("[Category photo]")
        tiles.append(con("card-category", [
            media,
            con("card-category-body", [heading(name, "card-category-name", "h3"), text(TILE_SUBS[name], "card-category-subs")]),
        ], url=cat_url(name)))
    categories = section("band", [wrap([section_head("Shop by category", "All categories", "/shop/"), con("category-tiles", tiles)])])

    def row(title, url, query, alt=False):
        return section("band" + (" band-alt" if alt else ""), [wrap([
            section_head(title, "View all", url),
            products("product-row", query),
        ])])

    best = row("Best Sellers", "/shop/?orderby=popularity", {"query_orderby": "popularity"})
    kitchen = row("Kitchen Favourites", cat_url("Kitchen & Dining"), {"query_include": ["terms"], "query_include_term_ids": [str(CAT_IDS["Kitchen & Dining"])]})
    sale = section("band", [wrap([con("sale-banner", [
        con("sale-banner-copy", [
            heading("Kitchen upgrade sale: up to 25% off", "section-heading heading-light", "h2"),
            text("Cookware, storage and serving pieces at our best prices. Offer ends [DATE].", "body-text-light"),
            button("Shop the sale", cat_url("Kitchen & Dining"), "button-light"),
        ]),
        placeholder("[Sale banner photo]", "sale-banner-photo"),
    ])])])
    decor = row("Home Decor Picks", cat_url("Home Decor"), {"query_include": ["terms"], "query_include_term_ids": [str(CAT_IDS["Home Decor"])]}, alt=True)
    about = section("band", [wrap([con("split", [
        con("split-copy", [
            heading("Everything your home needs, in one place", "section-heading", "h2"),
            text("[Short introduction to Castore Collection Kenya.]", "body-text"),
            button("About us", "/about/", "button-outline"),
        ]),
        placeholder("[About photo]", "split-media"),
    ])])])
    reviews = section("band band-alt", [wrap([
        section_head("What our customers say"),
        con("review-row", [con("card-review", [
            text("[Real customer review]", "review-quote"),
            con("stack", [heading("[Customer name]", "review-name", "p"), heading("[Town]", "review-town", "p")]),
        ]) for _ in range(3)]),
    ])])
    signup = section("band", [wrap([con("cta-whatsapp", [
        con("cta-whatsapp-copy", [
            heading("Get new arrivals and deals first", "section-heading", "h2"),
            text("Join our WhatsApp channel for new arrivals and deals.", "body-text"),
        ]),
        button("Join on WhatsApp", "/whatsapp-channel/", "button-whatsapp", icon("fab fa-whatsapp", "fa-brands")),
    ])])])
    return [hero, trust, categories, best, kitchen, sale, decor, about, reviews, signup]


# =========================================================
# INNER PAGES
# =========================================================
def page_banner(title, eyebrow=None, lead=None):
    kids = []
    if eyebrow:
        kids.append(heading(eyebrow, "eyebrow", "p"))
    kids.append(heading(title, "section-heading", "h1"))
    if lead:
        kids.append(text(lead, "lead"))
    return section("page-banner", [wrap([con("stack", kids)])])


def about_page():
    return [
        section("band", [wrap([con("split", [
            con("split-copy", [
                heading("About Castore", "eyebrow", "p"),
                heading("Better products. Better living.", "heading-hero", "h1"),
                text("[Opening paragraph: who Castore Collection is and who you serve.]", "lead"),
            ]),
            placeholder("[About photo: team, store or packed orders]", "split-media"),
        ])])]),
        section("band band-alt", [wrap([
            section_head("Everything your home needs, in one place"),
            con("value-row", [
                icon_box(icon("fas fa-check-circle"), "Quality checked", "[How you choose and check products]", "trust-item"),
                icon_box(icon("fas fa-truck"), "Countrywide delivery", "Nairobi in [X] days, countrywide in [X] days", "trust-item"),
                icon_box(icon("fab fa-whatsapp", "fa-brands"), "WhatsApp support", "[PHONE NUMBER]", "trust-item", "/whatsapp/"),
            ]),
        ])]),
        section("band", [wrap([con("split", [
            placeholder("[Photo: your store or location]", "split-media"),
            con("split-copy", [
                heading("Our story", "eyebrow", "p"),
                heading("[Story heading]", "section-heading", "h2"),
                text("[Your story: when you started, where you are based in [LOCATION], and what you care about.]", "body-text"),
                con("section-head", [button("Shop now", "/shop/", "button-primary"), button("Contact", "/contact/", "button-outline")]),
            ]),
        ])])]),
    ]


def contact_page():
    form = widget("form", {
        "form_name": "Contact",
        "form_fields": [
            {"_id": rid(), "custom_id": "name", "field_type": "text", "field_label": "Name", "placeholder": "", "required": "true", "width": "50"},
            {"_id": rid(), "custom_id": "phone", "field_type": "tel", "field_label": "Phone number", "placeholder": "07XX XXX XXX", "width": "50"},
            {"_id": rid(), "custom_id": "email", "field_type": "email", "field_label": "Email", "placeholder": "", "required": "true", "width": "100"},
            {"_id": rid(), "custom_id": "message", "field_type": "textarea", "field_label": "Message", "placeholder": "", "required": "true", "width": "100", "rows": 5},
        ],
        "button_text": "Send message",
        "show_labels": "true",
        "submit_actions": ["email"],
        "email_subject": "New message from the Castore Collection website",
        "success_message": "Thank you. We will get back to you soon.",
    }, "site-form")
    side = con("two-col-side", [
        con("card-panel", [
            icon_box(icon("fas fa-phone"), "Phone", "[PHONE NUMBER]", "trust-item"),
            icon_box(icon("fab fa-whatsapp", "fa-brands"), "WhatsApp", "[PHONE / WHATSAPP]", "trust-item", "/whatsapp/"),
            icon_box(icon("far fa-envelope", "fa-regular"), "Email", "[EMAIL]", "trust-item"),
            icon_box(icon("fas fa-map-marker-alt"), "Location", "[LOCATION], Kenya", "trust-item"),
        ]),
        placeholder("[Map or store photo]", "split-media"),
    ])
    return [
        page_banner("Contact us"),
        section("band band-tight", [wrap([con("two-col", [
            con("two-col-main card-panel", [heading("Send us a message", "heading-card", "h2"), form]),
            side,
        ])])]),
    ]


FAQ = [
    ("Ordering & payment", [("[Question about ordering]", "[Answer]"), ("[Question about paying with M-Pesa]", "[Answer]")]),
    ("Delivery", [("[Question about delivery times]", "[Answer: Nairobi in [X] days, countrywide in [X] days]"), ("[Question about delivery fees]", "[Answer]")]),
    ("Returns", [("[Question about returns]", "[Answer]"), ("[Question about refunds]", "[Answer]")]),
]


def faq_page():
    groups = []
    for title, qs in FAQ:
        acc = widget("nested-accordion", {"items": [{"_id": rid(), "item_title": q} for q, _ in qs], "default_state": "all_collapsed", "title_tag": "h3", "faq_schema": "",
                                          "accordion_item_title_icon": icon("fas fa-plus"), "accordion_item_title_icon_active": icon("fas fa-minus")}, "faq-list")
        acc["elements"] = [con("faq-answer", [text(a, "body-text")]) for _, a in qs]
        groups.append(con("stack", [heading(title, "drawer-label", "h2"), acc]))
    return [
        page_banner("Frequently asked questions"),
        section("band band-tight", [wrap(groups + [con("cta-whatsapp", [
            con("cta-whatsapp-copy", [heading("Still have a question?", "heading-card", "h2"), text("Chat with us on WhatsApp: [PHONE NUMBER]", "body-text")]),
            button("Contact us", "/contact/", "button-dark"),
        ])], "wrap-text")]),
    ]


def track_page():
    return [
        page_banner("Track your order", "Where is my parcel?", "Enter your order number and the email address you used at checkout."),
        section("band band-tight", [wrap([
            con("card-panel track-order-form", [widget("shortcode", {"shortcode": "[woocommerce_order_tracking]"})]),
            heading("Can't find your order? Chat with us on WhatsApp", "text-link", "p", "/whatsapp/"),
        ], "wrap-text")]),
    ]


def policy_template():
    """Theme Builder single-page template used by the four policy pages."""
    return [
        section("band band-tight", [wrap([con("policy-layout", [
            link_list(POLICIES, "link-list policy-nav"),
            con("policy-body", [
                widget("theme-page-title", {"header_size": "h1"}, "section-heading"),
                widget("theme-post-content", {}, "body-text policy-content"),
            ]),
        ])])]),
    ]


POLICY_BODY = """<p><em>Last updated: [DATE]</em></p>
<p>[Introduction to this policy.]</p>
<h2>[Section heading]</h2>
<p>[Policy text.]</p>
<ul><li>[Point]</li><li>[Point]</li><li>[Point]</li></ul>
<h2>[Section heading]</h2>
<p>[Policy text.]</p>
<h2>Questions</h2>
<p>Contact us on [PHONE / WHATSAPP] or [EMAIL].</p>"""


def main():
    os.makedirs(OUT, exist_ok=True)
    docs = {"header": header(), "footer": footer(), "mega": mega(), "drawer": drawer(), "home": home(), "about": about_page(),
            "contact": contact_page(), "faq": faq_page(), "track": track_page(), "policy-template": policy_template()}
    for name, tree in docs.items():
        with open(os.path.join(OUT, name + ".json"), "w") as f:
            json.dump(tree, f, ensure_ascii=False)
    with open(os.path.join(OUT, "policy-body.html"), "w") as f:
        f.write(POLICY_BODY)
    print({k: len(json.dumps(v)) for k, v in docs.items()})


if __name__ == "__main__":
    main()
