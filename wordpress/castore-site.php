<?php
/**
 * Plugin Name: Castore Collection site tweaks
 * Description: Self-hosted fonts, the site stylesheet, product-card buttons, Buy now, category chips, WhatsApp links and product-only search for Castore Collection Kenya.
 * Version: 1.0.0
 *
 * Installed as a must-use plugin (wp-content/mu-plugins/castore-site.php).
 * Source: https://github.com/wainainasam650-droid/castorecollections/tree/main/wordpress
 *
 * Settings (WordPress options, edit with WP-CLI or a plugin such as "Options"):
 *   castore_whatsapp_number   digits only, e.g. 2547XXXXXXXX. Empty = WhatsApp links open the Contact page.
 *   castore_whatsapp_channel  full URL of the WhatsApp channel. Empty = link opens the Contact page.
 */

defined( 'ABSPATH' ) || exit;

const CASTORE_CSS_DIR = 'castore';

/* ---------- Stylesheet + self-hosted fonts (uploads/castore/) ---------- */
add_action( 'wp_enqueue_scripts', function () {
	$uploads = wp_get_upload_dir();
	$file    = trailingslashit( $uploads['basedir'] ) . CASTORE_CSS_DIR . '/castore-site.css';
	if ( file_exists( $file ) ) {
		$deps = array();
		foreach ( array( 'astra-theme-css', 'woocommerce-general', 'elementor-frontend' ) as $handle ) {
			if ( wp_style_is( $handle, 'registered' ) ) {
				$deps[] = $handle;
			}
		}
		wp_enqueue_style( 'castore-site', trailingslashit( $uploads['baseurl'] ) . CASTORE_CSS_DIR . '/castore-site.css', $deps, (string) filemtime( $file ) );
	}
}, 20 );

add_action( 'wp_head', function () {
	$base = trailingslashit( wp_get_upload_dir()['baseurl'] ) . CASTORE_CSS_DIR . '/fonts/';
	foreach ( array( 'figtree-latin.woff2', 'fraunces-latin.woff2' ) as $font ) {
		printf( '<link rel="preload" href="%s" as="font" type="font/woff2" crossorigin>' . "\n", esc_url( $base . $font ) );
	}
}, 2 );

/* ---------- WhatsApp links: /whatsapp/ and /whatsapp-channel/ ---------- */
add_action( 'template_redirect', function () {
	$path = trim( (string) wp_parse_url( $_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH ), '/' );
	if ( 'whatsapp' !== $path && 'whatsapp-channel' !== $path ) {
		return;
	}
	$contact = home_url( '/contact/' );
	if ( 'whatsapp-channel' === $path ) {
		$channel = esc_url_raw( (string) get_option( 'castore_whatsapp_channel', '' ) );
		wp_redirect( $channel ? $channel : $contact, 302, 'Castore' );
		exit;
	}
	$number = preg_replace( '/\D+/', '', (string) get_option( 'castore_whatsapp_number', '' ) );
	if ( ! $number ) {
		wp_safe_redirect( $contact );
		exit;
	}
	$text       = 'Hello Castore Collection';
	$product_id = isset( $_GET['product'] ) ? absint( $_GET['product'] ) : 0;
	if ( $product_id && 'product' === get_post_type( $product_id ) ) {
		$text = sprintf( 'Hello Castore Collection, I have a question about %s: %s', get_the_title( $product_id ), get_permalink( $product_id ) );
	}
	wp_redirect( 'https://wa.me/' . $number . '?text=' . rawurlencode( $text ), 302, 'Castore' );
	exit;
} );

/* ---------- Search returns products ---------- */
add_action( 'pre_get_posts', function ( $query ) {
	if ( ! is_admin() && $query->is_main_query() && $query->is_search() && ! $query->get( 'post_type' ) ) {
		$query->set( 'post_type', 'product' );
	}
} );

/* ---------- Product card: sale badge, Add to cart + Buy now side by side ---------- */
add_filter( 'woocommerce_sale_flash', function ( $html, $post, $product ) {
	$regular = (float) $product->get_regular_price();
	$sale    = (float) $product->get_sale_price();
	if ( $product->is_type( 'variable' ) ) {
		$regular = (float) $product->get_variation_regular_price( 'max' );
		$sale    = (float) $product->get_variation_sale_price( 'min' );
	}
	if ( $regular > 0 && $sale > 0 && $sale < $regular ) {
		$percent = (int) round( ( $regular - $sale ) / $regular * 100 );
		return '<span class="onsale badge-sale">-' . $percent . '%</span>';
	}
	return '<span class="onsale badge-sale">Sale</span>';
}, 99, 3 );

function castore_buy_now_url( $product ) {
	if ( $product && $product->is_type( 'simple' ) && $product->is_purchasable() && $product->is_in_stock() ) {
		return add_query_arg( 'add-to-cart', $product->get_id(), wc_get_checkout_url() );
	}
	return $product ? $product->get_permalink() : '';
}

add_filter( 'woocommerce_loop_add_to_cart_link', function ( $html, $product ) {
	$buy = sprintf(
		'<a href="%s" class="button buy-now-button" aria-label="%s">Buy now</a>',
		esc_url( castore_buy_now_url( $product ) ),
		esc_attr( sprintf( 'Buy %s now', $product->get_name() ) )
	);
	return '<div class="card-product-actions">' . $html . $buy . '</div>';
}, 10, 2 );

add_filter( 'woocommerce_product_add_to_cart_text', function ( $text, $product ) {
	return ( $product->is_type( 'simple' ) && $product->is_purchasable() && $product->is_in_stock() ) ? 'Add to cart' : $text;
}, 10, 2 );

/* Buy now from the single product page goes straight to checkout. */
add_action( 'woocommerce_after_add_to_cart_button', function () {
	global $product;
	if ( $product && $product->is_type( 'simple' ) ) {
		echo '<button type="submit" name="castore_buy_now" value="1" class="button alt buy-now-single">Buy now</button>';
	}
} );
add_filter( 'woocommerce_add_to_cart_redirect', function ( $url ) {
	return ! empty( $_REQUEST['castore_buy_now'] ) ? wc_get_checkout_url() : $url;
} );

/* M-Pesa, delivery and WhatsApp notes under the add-to-cart form. */
add_action( 'woocommerce_single_product_summary', function () {
	global $product;
	if ( ! $product ) {
		return;
	}
	$ask = add_query_arg( 'product', $product->get_id(), home_url( '/whatsapp/' ) );
	echo '<div class="product-assurance">';
	echo '<p><strong>Pay with M-Pesa</strong> on checkout.</p>';
	echo '<p><strong>Delivery:</strong> Nairobi in [X] days, countrywide in [X] days. Free delivery within Nairobi on orders over KSh [AMOUNT].</p>';
	echo '<a class="ask-whatsapp" href="' . esc_url( $ask ) . '">Ask about this product on WhatsApp</a>';
	echo '</div>';
}, 35 );

add_filter( 'woocommerce_product_tabs', function ( $tabs ) {
	$tabs['castore_delivery'] = array(
		'title'    => 'Delivery',
		'priority' => 30,
		'callback' => function () {
			echo '<p>Nairobi in [X] days, countrywide in [X] days. Free delivery within Nairobi on orders over KSh [AMOUNT].</p>';
			echo '<p><a href="' . esc_url( home_url( '/delivery-information/' ) ) . '">Read our delivery information</a></p>';
		},
	);
	$tabs['castore_returns']  = array(
		'title'    => 'Returns',
		'priority' => 40,
		'callback' => function () {
			echo '<p>[Returns summary]</p>';
			echo '<p><a href="' . esc_url( home_url( '/returns-and-refunds/' ) ) . '">Read our returns and refunds policy</a></p>';
		},
	);
	unset( $tabs['reviews'] );
	return $tabs;
} );

/* ---------- Category pages: subcategories as chips ---------- */
add_action( 'woocommerce_archive_description', function () {
	if ( ! is_product_category() ) {
		return;
	}
	$term     = get_queried_object();
	$children = get_terms( array( 'taxonomy' => 'product_cat', 'parent' => $term->term_id, 'hide_empty' => false, 'orderby' => 'meta_value_num', 'meta_key' => 'order' ) );
	if ( is_wp_error( $children ) || ! $children ) {
		return;
	}
	echo '<nav class="category-chips" aria-label="Subcategories">';
	foreach ( $children as $child ) {
		printf( '<a href="%s">%s</a>', esc_url( get_term_link( $child ) ), esc_html( $child->name ) );
	}
	echo '</nav>';
}, 20 );
