var contador = 0;

fun classifica(n) {
  if n <= 0 { return 0; } else {}
  if n >= 100 { return 2; } else {}
  return 1;
}

main {
  contador += classifica(0 - 5);
  contador += classifica(50);
  contador += classifica(150);
  return contador;
}
