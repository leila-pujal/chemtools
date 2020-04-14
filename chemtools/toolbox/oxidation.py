# -*- coding: utf-8 -*-
# ChemTools is a collection of interpretive chemical tools for
# analyzing outputs of the quantum chemistry calculations.
#
# Copyright (C) 2016-2019 The ChemTools Development Team
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
"""Module for Oxidation State."""


from chemtools.wrappers.molecule import Molecule
from chemtools.wrappers.grid import MolecularGrid
from chemtools.wrappers.part import DensPart

import numpy as np
import itertools

from operator import itemgetter


class EOS(object):
    def __init__(self, molecule, part, grid):
        self.molecule = molecule
        self.part = part
        self.grid = grid
        self._frags = None

    @classmethod
    def from_molecule(cls, molecule, part, grid):
        """Initialize class from `Molecule` object.

        Parameters
        ----------
        molecule : `Molecule`
            Instance of `Molecular` class.
        part : `DensPart`
            Instance of `DensPart` class.
        grid : `MolecularGrid`
            Molecular numerical integration grid.

        """
        return cls(molecule, part, grid)

    @classmethod
    def from_file(cls, fname, part, grid):
        """Initialize class using wave-function file.

        Parameters
        ----------
        fname : str
            A string representing the path to a molecule's fname.
        part : `DensPart`
            Instance of `DensPart` class.
        grid : `MolecularGrid`
            Molecular numerical integration grid.

        """
        molecule = Molecule.from_file(fname)
        return cls.from_molecule(molecule, part, grid)

    def compute_fragment_overlap(self, fragments=None, spin='ab'):
        # compute MO overlap matrix for fragments

        if spin == 'a':
            ne = int(self.molecule.mo.nelectrons[0])
        elif spin == 'b':
            ne = int(self.molecule.mo.nelectrons[1])
        else:
            raise NotImplementedError('Not clear what to do here!')

        # defining fragments/atoms
        if fragments is None:
           self._frags = [[index] for index in range(len(self.molecule.numbers))]
        else:
            self._frags = fragments

        orbitals = self.molecule.compute_molecular_orbital(self.grid.points, spin=spin).T

        # generating qij array for each atom/fragment
        arr = np.zeros((len(self._frags), ne, ne))

        for i, j in itertools.combinations_with_replacement(range(ne), 2):
            qij = self.part.condense_to_fragments(orbitals[i] * orbitals[j], self._frags, w_power=2)
            for x in range(len(self._frags)):
                arr[x][i][j] = qij[x]
                arr[x][j][i] = qij[x]

        return arr

    def compute_fragment_occupation(self, fragments=None, spin='ab'):
        # computes effective orbitals occupation for each fragment passed

        # compute fragment overlap matrix
        arr = self.compute_fragment_overlap(fragments, spin=spin)

        # diagonalize overlap matrix
        _, s, _ = np.linalg.svd(arr)

        np.set_printoptions(suppress=True)
        print 'alpha occupations', s
        # for i in s_a:
        # print i

#      print 'beta occupations'
#      for i in s_b:
#        print i

        return s

    def compute_oxidation_state(self, fragments=None):

        # compute oxidation state for fragments

        nalpha = int(self.molecule.mo.nelectrons[0])
        nbeta = int(self.molecule.mo.nelectrons[1])

        # TODO: avoid repeated calculation for restricted case
        s_a = self.compute_fragment_occupation(fragments, spin='a')
        s_b = self.compute_fragment_occupation(fragments, spin='b')

        sorted_alpha = sorted([(s, i) for i, row in enumerate(s_a) for s in row], reverse=True)
        sorted_beta = sorted([(s, i) for i, row in enumerate(s_b) for s in row], reverse=True)

        # occupations_alpha = []
        # occupations_beta = []
        #
        # for a in range(len(self._frags)):
        #     for i in range(nalpha):
        #         occupations_alpha.append((s_a[a][i], a))
        #
        # for a in range(len(self._frags)):
        #     for i in range(nbeta):
        #         occupations_beta.append((s_b[a][i], a))
        #
        # sorted_alpha = sorted(occupations_alpha, key=itemgetter(0), reverse=True)
        # sorted_beta = sorted(occupations_beta, key=itemgetter(0), reverse=True)

        occs_a = [item[1] for item in sorted_alpha]
        occs_b = [item[1] for item in sorted_beta]

        occs_frag_a = [occs_a[:nalpha].count(index) for index in range(len(self._frags))]
        occs_frag_b = [occs_b[:nbeta].count(index) for index in range(len(self._frags))]

        z_frag = [sum([self.molecule.numbers[index] for index in frag]) for frag in self._frags]
        oxidation = np.array(z_frag) - np.array(occs_frag_a) - np.array(occs_frag_b)

#         s_a_occ = [[] for _ in range(len(self._frags))]
#         s_b_occ = [[] for _ in range(len(self._frags))]
#
#         s_a_uncc = [[] for _ in range(len(self._frags))]
#         s_b_uncc = [[] for _ in range(len(self._frags))]
#
#         lo_a = 0
#         print s_a_occ
#         for index, e in enumerate(sorted_alpha):
#             if index < nalpha:
#                 s_a_occ[e[1]].append(e)
#                 lo_a = index
#             else:
#                 s_a_uncc[e[1]].append(e)
#
#         lo_b = 0
#         for index, e in enumerate(sorted_beta):
#             if index < nbeta:
#                 s_b_occ[e[1]].append(e)
#                 lo_b = index
#             else:
#                 s_b_uncc[e[1]].append(e)
#
#         # Reliability index
#         r_alpha = 0
#         fu_a = lo_a + 1
#         if len(self._frags) == 1:
#             r_alpha = 100.000
#         else:
#             while True:
#                 if sorted_alpha[lo_a][1] == sorted_alpha[fu_a][1]:
#                     fu_a = fu_a + 1
#                 else:
#                     break
#
#         r_beta = 0
#         fu_b = lo_b + 1
#         if len(self._frags) == 1:
#             r_beta = 100.000
#         else:
#             while True:
#                 if sorted_beta[lo_b][1] == sorted_beta[fu_b][1]:
#                     fu_b = fu_b + 1
#                 else:
#                     break
#
#             r_alpha = 100 * (sorted_alpha[lo_a][0] - sorted_alpha[fu_a][0] + 0.5)
#             r_beta = 100 * (sorted_beta[lo_b][0] - sorted_beta[fu_b][0] + 0.5)
#
#         for a in range(len(self._frags)):
#             print 'Fragment', a, 'net occupations'
#             print 'alpha occupied ', s_a_occ[a]
#             print 'alpha unoccupied ', s_a_uncc[a]
#             print
#             print 'beta occupied ', s_b_occ[a]
#             print 'beta unocupied ', s_b_uncc[a]
#             print
#
# #     print(sorted_alpha[lo_a], sorted_alpha[fu_a], r_alpha)
# #     print(sorted_beta[lo_b], sorted_beta[fu_b], r_beta)
#
#         print 'Reliability index R(%) =', r_alpha, r_beta
#         print 'Fragment', '    ', 'oxidation state'
#         oxidation = []
#         for a in range(len(self._frags)):
#             occ = len(s_a_occ[a]) + len(s_b_occ[a])
#             z = 0
#             if fragments is None:
#                 z = self.molecule.numbers[a]
#             else:
#                 for elem in self._frags[a]:
#                     z = z + self.molecule.numbers[elem]
#
#             os = z - occ
#             oxidation.append([os, a])
#             print a, '    ', os
#        print oxidation

        return oxidation

    def compute_effective_orbital(self):
        pass
