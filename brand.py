from flask import Blueprint, render_template, current_app, abort, url_for, g, \
    request, session, redirect
from flask_paginate import Pagination
from flask_babel import gettext as _, lazy_gettext
from galatea.tryton import tryton
from catalog.catalog import catalog_ordered

brand = Blueprint('brand', __name__, template_folder='templates')

DISPLAY_MSG = lazy_gettext('Displaying <b>{start} - {end}</b> of <b>{total}</b>')

GALATEA_WEBSITE = current_app.config.get('TRYTON_GALATEA_SITE')
SHOP = current_app.config.get('TRYTON_SALE_SHOP')
LIMIT = current_app.config.get('TRYTON_PAGINATION_CATALOG_LIMIT', 20)

Website = tryton.pool.get('galatea.website')
ProductBrand = tryton.pool.get('product.brand')
Template = tryton.pool.get('product.template')

BRAND_TEMPLATE_FILTERS = []

@brand.route("/<slug>", endpoint="brand")
@tryton.transaction()
def brand_products(lang, slug):
    '''Products by brand'''
    websites = Website.search([
        ('id', '=', GALATEA_WEBSITE),
        ], limit=1)
    if not websites:
        abort(404)
    website, = websites

    product_brands = ProductBrand.search([('slug', '=', slug)], limit=1)
    if not product_brands:
        # change 404 to all brand list
        return redirect(url_for('.brands', lang=g.language))
    else:
        product_brand = product_brands[0]

    # limit
    if request.args.get('limit'):
        try:
            limit = int(request.args.get('limit'))
            session['catalog_limit'] = limit
        except:
            limit = LIMIT
    else:
        limit = session.get('catalog_limit', LIMIT)

    # view
    if request.args.get('view'):
        view = 'grid'
        if request.args.get('view') == 'list':
            view = 'list'
        session['catalog_view'] = view

    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    domain_filter = session.get('brand_filter', [])
    if request.form:
        domain_filter = []
        domain_filter_keys = set()
        for k, v in request.form.iteritems():
            if k in BRAND_TEMPLATE_FILTERS:
                domain_filter_keys.add(k)

        for k in list(domain_filter_keys):
            domain_filter.append((k, 'in', request.form.getlist(k)))

    session['brand_filter'] = domain_filter

    domain = [
        ('esale_available', '=', True),
        ('esale_active', '=', True),
        ('shops', 'in', [SHOP]),
        ('brand', '=', product_brand),
        ] + domain_filter
    total = Template.search_count(domain)
    offset = (page-1)*limit

    products = Template.search(domain, offset, limit, order=catalog_ordered())

    pagination = Pagination(page=page, total=total, per_page=limit, display_msg=DISPLAY_MSG, bs_version='3')

    #breadcumbs
    breadcrumbs = [{
        'slug': url_for('catalog.catalog', lang=g.language),
        'name': _('Catalog'),
        }, {
        'slug': url_for('.brands', lang=g.language),
        'name': _('Brands'),
        }, {
        'slug': url_for('.brand', lang=g.language, slug=slug),
        'name': product_brand.name,
        }]

    return render_template('catalog-brand.html',
            website=website,
            brand=product_brand,
            breadcrumbs=breadcrumbs,
            pagination=pagination,
            products=products,
            )

@brand.route("/", endpoint="brands")
@tryton.transaction()
def brand_all(lang):
    '''All brands'''
    websites = Website.search([
        ('id', '=', GALATEA_WEBSITE),
        ], limit=1)
    if not websites:
        abort(404)
    website, = websites

    brands = ProductBrand.search([])

    #breadcumbs
    breadcrumbs = [{
        'slug': url_for('catalog.catalog', lang=g.language),
        'name': _('Catalog'),
        }, {
        'slug': url_for('.brands', lang=g.language),
        'name': _('Brands'),
        }]

    return render_template('catalog-brands.html',
            website=website,
            brands=brands,
            breadcrumbs=breadcrumbs,
            )
