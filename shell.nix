{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (ps: with ps; [
      pandas
      numpy
      matplotlib
      yfinance
      statsmodels
      scikit-learn
      jupyter
    ]))
    pkgs.git
  ];
}
