fun classificaIdade(idade) {
  if idade <= 12 { return 0; } else {}
  if idade >= 60 { return 2; } else {}
  return 1;
}

main {
  return classificaIdade(70);
}
