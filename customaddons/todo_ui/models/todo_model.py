# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons.base.res.res_request import referenceable_models
from openerp.exceptions import ValidationError




class Tag(models.Model):
    _name = 'todo.task.tag'
    name = fields.Char('Name', size=40, translate=True)

    # Many2many inverse relation
    task_ids = fields.Many2many('todo.task', string='Tasks')

    # Hierarchic relations:
    _parent_store = True
    _parent_name = 'parent_id'  # the default
    parent_id = fields.Many2one(
        'todo.task.tag', 'Parent Tag', ondelete='restrict')
    parent_left = fields.Integer('Parent Left', index=True)
    parent_right = fields.Integer('Parent Right', index=True)
    child_ids = fields.One2many('todo.task.tag', 'parent_id', 'Child Tags')


class Stage(models.Model):
    _name = 'todo.task.stage'
    _order = 'sequence,name'
    _rec_name = 'name'  # the default
    _table_name = 'todo_task_stage'  # the default

    # Field attributes:
    name = fields.Char(
        string='Name',
        # Common field attributes:
        copy=False,
        default='New',
        groups="base.group_user,base.group_no_one",
        help='The title for the stage.',
        index=True,
        readonly=False,
        required=True,
        states={'done': [('readonly', False)]},
        # String only attributes:
        size=40,
        translate=True,
    )

    # Other string fields:
    desc = fields.Text('Description')
    state = fields.Selection(
        [('draft', 'New'), ('open', 'Started'), ('done', 'Closed')],
        'State',
        # selection_add= When extending a Model, adds items to selection list
    )
    docs = fields.Html('Documentation')

    # Numeric fields:
    sequence = fields.Integer('Sequence')
    perc_complete = fields.Float('% Complete', (3, 2))

    # Date fields:
    date_effective = fields.Date('Effective Date')
    date_changed = fields.Datetime('Last Changed')

    # Other fields:
    fold = fields.Boolean('Folded?')
    image = fields.Binary('Image')

    # One2many inverse relation:
    task_ids = fields.One2many('todo.task', 'stage_id', 'Tasks in this stage')


class TodoTask(models.Model):
    _inherit = 'todo.task'

    # Relational fields
    stage_id = fields.Many2one('todo.task.stage', 'Stage')
    tag_ids = fields.Many2many(
        'todo.task.tag',      # related= (model name)
        'todo_task_tag_rel',  # relation= (table name)
        'task_id',               # column1= ("this" field)
        'tag_id',                # column2= ("other" field)
        string='Tags',

        # Relational field attributes:
        auto_join=False,
        context="{}",
        domain="[]",
        ondelete='cascade',
    )


    # Dynamic Reference fields:
    refers_to = fields.Reference(
        # Set a Selection list, such as:
        # [('res.user', 'User'), ('res.partner', 'Partner')],
        # Or use standard "Referencable Models":
        referenceable_models,
        'Refers to',  # string= (title)
    )
    # Related fields:
    stage_state = fields.Selection(
        related='stage_id.state',
        string='Stage State',
        store=True,  # optional
    )
    # Calculated fields:
    stage_fold = fields.Boolean(
        string='Stage Folded?',
        compute='_compute_stage_fold',
        search='_search_stage_fold',
        inverse='_write_stage_fold',
        store=False,  # the default
    )

    @api.one
    @api.depends('stage_id.fold')
    def _compute_stage_fold(self):
        self.stage_fold = self.stage_id.fold

    def _search_stage_fold(self, operator, value):
        return [('stage_id.fold', operator, value)]

    def _write_stage_fold(self):
        self.stage_id.fold = self.stage_fold

    # Constraints
    _sql_constraints = [(
        'todo_task_name_unique',
        'UNIQUE (name, user_id, active)',
        'Task title must be unique!'
    )]

    @api.one
    @api.constrains('name')
    def _check_name_size(self):
        if len(self.name) < 5:
            raise ValidationError('Title must have 5 chars!')

    @api.one
    def compute_user_todo_count(self):
        self.user_todo_count = self.search_count(
            [('user_id', '=', self.user_id.id)])

    user_todo_count = fields.Integer(
        'User To-Do Count',
        compute='compute_user_todo_count'
    )
    effort_estimate = fields.Integer('Effort Estimate')

