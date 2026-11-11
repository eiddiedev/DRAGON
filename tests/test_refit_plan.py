"""Protect the editor's unusual world-space child transforms and user edits."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from apply_refit_plan import transform_document


class PlacementTests(unittest.TestCase):
    def setUp(self):
        self.doc = dict(audioData={'uri': 'keep'}, runtimeScripts={'main': 'keep'},
                        nodeTransformDatas=[self.node(1, 0), self.node(2, 1), self.node(3, 2), self.node(4, 0)])
        self.plan = dict(moves=[dict(id=1, name='node1', before=dict(x=1, y=2, z=3), after=dict(x=10, y=20, z=30))], disable=[], meshes=[])

    def node(self, nid, parent):
        return dict(id=nid, parentId=parent, nodeName=f'node{nid}', pos=dict(x=nid,y=2*nid,z=3*nid),
                    rot=dict(x=0,y=.5,z=0,w=.866), scale=dict(x=2,y=2,z=2), isActive=True)

    def test_descendants_keep_offsets_and_unrelated_state(self):
        original = copy.deepcopy(self.doc)
        result, report = transform_document(self.doc, self.plan)
        self.assertEqual(self.doc, original)
        for before, after in zip(original['nodeTransformDatas'][:3], result['nodeTransformDatas'][:3]):
            self.assertEqual(after['pos'], {a:before['pos'][a]+d for a,d in zip('xyz',(9,18,27))})
            self.assertEqual(before['rot'], after['rot'])
            self.assertEqual(before['scale'], after['scale'])
        for key in ('audioData','runtimeScripts'):
            self.assertEqual(result[key], original[key])
        self.assertEqual(result['nodeTransformDatas'][3], original['nodeTransformDatas'][3])
        self.assertEqual(report['translated_nodes'], 3)

    def test_user_move_rejects_stale_plan(self):
        self.doc['nodeTransformDatas'][0]['pos']['y'] += 1
        with self.assertRaisesRegex(ValueError, 'moved since planning'):
            transform_document(self.doc, self.plan)

    def test_disabling_root_disables_all_descendants(self):
        self.plan.update(moves=[], disable=[dict(id=1,name='node1')])
        result, _ = transform_document(self.doc, self.plan)
        self.assertEqual([n['isActive'] for n in result['nodeTransformDatas']], [False,False,False,True])


if __name__ == '__main__':
    unittest.main()
