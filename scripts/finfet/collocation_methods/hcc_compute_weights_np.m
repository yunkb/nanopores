function w = hcc_compute_weights_np ( n, np, p )

%*****************************************************************************80
%
%% HCC_COMPUTE_WEIGHTS_NP: weights of a Hermite-Cubic-Chebyshev-Spacing rule.
%
%  Discussion:
%
%    For the HCC rule, we assume that an interval has been divided by
%    M nodes X into Chebyshev-spaced subintervals, and that at each
%    abscissa both function and derivative information is available.
%    The piecewise cubic Hermite interpolant is constructed for this data.
%    The quadrature rule uses N = 2 * M abscissas, where each node is
%    listed twice, and the weights occur in pairs, with the first multiplying
%    the function value and the second the derivative.
%
%  Licensing:
%
%    This code is distributed under the GNU LGPL license.
%
%  Modified:
%
%    11 March 2011
%
%  Author:
%
%    John Burkardt
%
%  Parameters:
%
%    Input, integer N, the order of the rule.
%
%    Input, integer NP, the number of parameters.
%
%    Input, real P(NP), the parameters.
%
%    Output, real W(N), the weights.
%
  w = hcc_compute_weights ( n );

  return
end
