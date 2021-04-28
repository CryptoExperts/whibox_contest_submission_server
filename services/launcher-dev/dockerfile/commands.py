#!/usr/bin/env python3

import click
import hashlib
import random

from nist_p256 import NIST_P256


@click.command()
@click.argument('seed', default="CHES2021")
def cmd_keygen(seed):
    # CHES 2021 will start from September 12, 2021
    random.seed(seed)
    d = random.randint(1, NIST_P256.n-1)
    Q = NIST_P256.scalar_multiplication(d)

    print(f"seed: seed = {seed}")
    print(f"private key: d = {d:064X}")
    print(f"public key:  Q = ({repr(Q)})")
    print(f"encoded public key:  {Q}")

    return d, Q


@click.command()
@click.argument('pa_str', metavar="PUBLIC_KEY")
@click.argument('hash_', metavar="HASH")
@click.argument('signature', metavar="SIGNATURE")
def cmd_ecdsa_verify(pa_str: str, hash_: str, signature: str):
    if ecdsa_verify_str(pa_str, hash_, signature):
        print("Good signature :)")
    else:
        print("Wrong signature")
    return True


@click.command()
@click.argument('d_str', metavar="PRIVATE_KEY")
def cmd_ec_schnorr_sign(d_str: str):
    """Variables names follow BSI EC-Schnorr standardized"""
    d = decode_private(d_str)

    while True:
        # choose a random k
        k = random.randint(1, NIST_P256.n-1)

        # Q = k x G, r = Q[x]
        Q = NIST_P256.scalar_multiplication(k)
        Q_x = Q.x.val

        # h = SHA256(r)
        m = hashlib.sha256()
        m.update(bytes.fromhex(f"{Q_x:064x}"))
        r = int(m.hexdigest(), 16)
        if (r % NIST_P256.n) == 0:
            continue

        s = (k - r * d) % NIST_P256.n
        if s == 0:
            continue

        print("Signature:", f"{r:064X}{s:064X}")

        return r, s


@click.command()
@click.argument('pa_str', metavar="PUBLIC_KEY")
@click.argument('signature', metavar="SIGNATURE")
def cmd_ec_schnorr_verify(pa_str, signature):
    """Variables names follow BSI EC-Schnorr standardized"""
    P_A = decode_public(pa_str)
    if not check_public_key(P_A):
        return False

    r, s = decode_signature(signature)
    if not check_r_s(r, s):
        return False

    Q = NIST_P256.scalar_multiplication(s) + \
        NIST_P256.scalar_multiplication(r, P_A)
    if Q.is_at_infinity:
        print("Wrong signature")
        return False

    m = hashlib.sha256()
    m.update(bytes.fromhex(f"{Q.x.val:064x}"))
    v = int(m.hexdigest(), 16)

    print("Good signature :)" if r == v else "Wrong signature")
    return r == v


def decode_signature(signature):
    if len(signature) != 128:
        raise click.ClickException(
            "SIGNATURE should be 128 hexadecimal digits long.")
    try:
        r = int(signature[:32*2], 16)
        s = int(signature[32*2:], 16)
    except ValueError:
        raise click.ClickException(
            "PUBLIC_KEY is not in valid hex.")
    return r, s


def decode_private(d_str):
    try:
        d = int(d_str, 16)
    except ValueError:
        raise click.ClickException(
            "PRIVATE_KEY is not in valid hex.")
    return d


def decode_public(pa_str):
    if len(pa_str) != 128:
        raise click.ClickException(
            "PUBLIC_KEY should be 128 hexadecimal digits long.")
    try:
        pa_x = int(pa_str[:64], 16)
        pa_y = int(pa_str[64:], 16)
    except ValueError:
        raise click.ClickException(
            "PUBLIC_KEY is not in valid hex.")
    return NIST_P256.Point(NIST_P256.Modular(pa_x), NIST_P256.Modular(pa_y))


def check_public_key(Q: NIST_P256.Point):
    if Q.is_at_infinity:
        print("Public key should not be infinity")
        return False

    if not Q.is_on_curve:
        print("Public key is not on curve")
        return False

    point_infinity = NIST_P256.scalar_multiplication(NIST_P256.n, Q)
    if not point_infinity.is_at_infinity:
        print("Something wrong with the public key")
        return False

    return True


def check_r_s(r, s):
    n = NIST_P256.n

    if r < 1 or r > n-1:
        print("r is not between [1, n-1]")
        return False

    if s < 1 or s > n-1:
        print("s is not between [1, n-1]")
        return False

    return True


def ecdsa_verify_str(pa_str: str, hash_: str, signature: str):
    Q = decode_public(pa_str)
    hash_ = int(hash_, 16)
    r, s = decode_signature(signature)
    return ecdsa_verify(Q, hash_, (r, s))


def ecdsa_verify(Q: NIST_P256.Point, hash_: int, signature: (int, int)):
    if not check_public_key(Q):
        return False

    r, s = signature
    if not check_r_s(r, s):
        return False

    n = NIST_P256.n
    z = hash_ % n

    s_inv = int(pow(s, n-2, n))
    assert (s*s_inv) % n == 1
    u1 = (z * s_inv) % n
    u2 = (r * s_inv) % n

    P = NIST_P256.scalar_multiplication(u1) + \
        NIST_P256.scalar_multiplication(u2, Q)
    if P.is_at_infinity:
        print("Invalid signature")
        return False

    return (P.x.val % n) == r
