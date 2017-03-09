# -*- coding: utf-8 -*-
# ChemTools is a collection of interpretive chemical tools for
# analyzing outputs of the quantum chemistry calculations.
#
# Copyright (C) 2014-2015 The ChemTools Development Team
#
# This file is part of ChemTools.
#
# ChemTools is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# ChemTools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --
'''Orbital-Based Local Tools.'''


import numpy as np
from chemtools.tool.densitytool import DensityLocalTool


class OrbitalLocalTool(DensityLocalTool):
    '''
    Class of orbital-based local descriptive tools.
    '''
    def __init__(self, obasis, exp_alpha, exp_beta=None, points=None):
        r'''
        Parameters
        ----------
        obasis :
            A HORTON ''obasis'' object, an orbital basis and 
            instance of the GOBasis class.
        exp_alpha :
            An expansion of the alpha orbitals in a basis set,
            with orbital energies and occupation numbers.
        exp_beta : default=None
            An expansion of the beta orbitals in a basis set,
            with orbital energies and occupation numbers.
        points : default=None
            Gridpoints used to calculate the properties.
        '''

        self._obasis = obasis
        self._exp_alpha = exp_alpha

        if exp_beta is None:
            self._dm =  self._exp_alpha.to_dm(factor=2.0)
        else:
            self._exp_beta = exp_beta
            self._dm =  self._exp_alpha.to_dm(factor=1.0)
            self._exp_beta.to_dm(self._dm, factor=1.0, clear=False)

        self._points = points

        # Compute density & gradient on grid
        dens = self._obasis.compute_grid_density_dm(self._dm, self._points)
        grad = self._obasis.compute_grid_gradient_dm(self._dm, self._points)

        DensityLocalTool.__init__(self, dens, grad, hessian=None)


    @property
    def kinetic_energy_density(self):
        r'''
        positive definite kinetic energy density defined as:

        .. math::
           \tau \left(\mathbf{r}\right) = 
           \sum_i^N n_i \frac{1}{2} \rvert \nabla \phi_i \left(\mathbf{r}\right) \lvert^2
        '''
        return self._obasis.compute_grid_kinetic_dm(self._dm, self._points)

    @property
    def elf(self):
        r'''
        The Electron Localization Function introduced by Becke and Edgecombe:

        .. math::
            ELF (\mathbf{r}) =
                \frac{1}{\left( 1 + \left(\frac{D_{\sigma}(\mathbf{r})}
                {D_{\sigma}^0 (\mathbf{r})} \right)^2\right)} ,
        with
        
        .. math::
            D_{\sigma} (\mathbf{r}) =  \tau_{\sigma} (\mathbf{r}) -
                \frac{1}{4} \frac{(\nabla \rho_{\sigma})^2}{\rho_{\sigma}} .
        .. math::

            D_{\sigma}^0 (\mathbf{r}) =
                \frac{3}{5} (6 \pi^2)^{2/3} \rho_{\sigma}^{5/3} (\mathbf{r}) ,

        where :math:`\tau_{\sigma}` is the positive definite kinetic energy density:

        .. math::
            \tau_{\sigma} (\mathbf{r}) =
                \sum_i^{\sigma} \lvert \nabla \phi_i (\mathbf{r}) \rvert^2
        '''

        elfd = self.kinetic_energy_density - self.weizsacker_kinetic_energy_density
        tf = np.ma.masked_less(self.thomas_fermi_kinetic_energy_density, 1.0e-30)
        tf.filled(1.0e-30)

        return 1.0 / (1.0 + (elfd / tf)**2.0)

    def mep(self, coordinates, pseudo_numbers):
        r'''
        Molecular Electrostatic Potential defined as:

        .. math::
            V \left(\mathbf{r}\right) =
            \sum_A \frac{Z_A}{\rvert \mathbf{R}_A - \mathbf{r} \lvert}
            - \int \frac{\rho \left(\mathbf{r}'\right)}{\rvert \mathbf{r}' - \mathbf{r} \lvert} d\mathbf{r}'
        '''
        #compute mep
        return self._obasis.compute_grid_esp_dm(self._dm, coordinates, pseudo_numbers, self._points)
